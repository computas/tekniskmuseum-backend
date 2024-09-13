#! /usr/bin/env python
"""
    Tools for interacting with Azure Custom Vision and Azure Blob Storage
"""
import logging
import uuid
import time
import sys
import os
from typing import Dict
from typing import List
from src import models
from flask import current_app as app
import requests
from werkzeug import exceptions as excp
from msrest.authentication import ApiKeyCredentials
from azure.storage.blob import BlobServiceClient
from azure.cognitiveservices.vision.customvision.prediction import (
    CustomVisionPredictionClient,
)
from azure.cognitiveservices.vision.customvision.training import (
    CustomVisionTrainingClient,
)
from azure.cognitiveservices.vision.customvision.training.models import (
    ImageUrlCreateEntry,
    CustomVisionErrorException,
    ImageUrlCreateBatch
)

from utilities.keys import Keys
from utilities import setup


class Classifier:
    """
        Class for interacting with Custom Vision. Contatins three key methods:
            - predict_imgage() / predicts a an image
            - upload_images() / reads image URLs from Blob Storage and uploads to Custom Vision
            - train() / trains a model
    """

    def __init__(self) -> None:
        """
            Reads configuration file
            Initializes connection to Azure Custom Vision predictor and training resources.

            Parameters:
            blob_service_client: Azure Blob Service interaction client

            Returns:
            None
        """
        self.ENDPOINT = Keys.get("CV_ENDPOINT")
        self.PREDICTION_ENDPOINT = Keys.get("CV_PREDICTION_ENDPOINT")
        self.project_id = Keys.get("CV_PROJECT_ID")
        self.prediction_key = Keys.get("CV_PREDICTION_KEY")
        self.training_key = Keys.get("CV_TRAINING_KEY")
        self.base_img_url = Keys.get("BASE_BLOB_URL")
        self.prediction_resource_id = Keys.get("CV_PREDICTION_RESOURCE_ID")

        self.prediction_credentials = ApiKeyCredentials(
            in_headers={"Prediction-key": self.prediction_key}
        )
        self.predictor = CustomVisionPredictionClient(
            self.PREDICTION_ENDPOINT, self.prediction_credentials
        )
        self.training_credentials = ApiKeyCredentials(
            in_headers={"Training-key": self.training_key}
        )
        self.trainer = CustomVisionTrainingClient(
            self.ENDPOINT, self.training_credentials
        )
        connect_str = Keys.get("BLOB_CONNECTION_STRING")
        self.blob_service_client = BlobServiceClient.from_connection_string(
            connect_str
        )
        try:
            # get all project iterations
            iterations = self.trainer.get_iterations(self.project_id)
            # find published iterations
            puplished_iterations = [
                iteration
                for iteration in iterations
                if iteration.publish_name is not None
            ]
            # get the latest published iteration
            puplished_iterations.sort(key=lambda i: i.created)
            self.iteration_name = puplished_iterations[-1].publish_name

            with app.app_context():
                models.update_iteration_name(self.iteration_name)
        except Exception as e:
            logging.info(e)
            self.iteration_name = "Iteration5"

    def predict_image_url(self, img_url: str) -> Dict[str, float]:
        """
            Predicts label(s) of Image read from URL.

            Parameters:
            img_url: Image URL

            Returns:
            (prediction (dict[str,float]): labels and assosiated probabilities,
            best_guess: (str): name of the label with highest probability)
        """
        with app.app_context():
            self.iteration_name = models.get_iteration_name()
        res = self.predictor.classify_image_url(
            project_id=self.project_id,
            published_name=self.iteration_name,
            url=img_url,
            custom_headers={
                "Prediction-Key": self.prediction_key})
        pred_kv = dict([(i.tag_name, i.probability) for i in res.predictions])
        best_guess = max(pred_kv, key=pred_kv.get)

        return pred_kv, best_guess

    def predict_image(self, img) -> Dict[str, float]:
        """
            Predicts label(s) of Image read from URL.
            ASSUMES:
            -image of type .png
            -image size less than 4MB
            -image resolution at least 256x256 pixels

            Parameters:
            img_url: .png file

            Returns:
            (prediction (dict[str,float]): labels and assosiated probabilities,
            best_guess: (str): name of the label with highest probability)
        """
        with app.app_context():
            self.iteration_name = models.get_iteration_name()
        res = self.predictor.classify_image_with_no_store(
            self.project_id, self.iteration_name, img
        )
        # reset the file head such that it does not affect the state of the
        # file handle
        img.seek(0)
        pred_kv = dict([(i.tag_name, i.probability) for i in res.predictions])
        best_guess = max(pred_kv, key=pred_kv.get)
        return pred_kv, best_guess

    def predict_image_by_post(self, img) -> Dict[str, float]:
        """
            Predicts label(s) of Image read from URL.
            ASSUMES:
            -image of type .png
            -image size less than 4MB
            -image resolution at least 256x256 pixels

            Parameters:
            img_url: .png file

            Returns:
            (prediction (dict[str,float]): labels and assosiated probabilities,
            best_guess: (str): name of the label with highest probability)
        """

        headers = {'content-type': 'application/octet-stream',
                   "prediction-key": self.prediction_key}
        res = self.predictor.classify_image(
            self.project_id,
            self.iteration_name,
            img.read(),
            custom_headers=headers)
        # res = requests.post(Keys.get("CV_PREDICTION_ENDPOINT"), img.read(), headers=headers).json()

        img.seek(0)
        # pred_kv = dict([(i["tagName"], i["probability"]) for i in res["predictions"]])
        pred_kv = dict([(i.tag_name, i.probability) for i in res.predictions])
        best_guess = max(pred_kv, key=pred_kv.get)
        return pred_kv, best_guess

    def __chunks(self, lst, n):
        """
            Helper method used by upload_images() to upload URL chunks of 64, which is maximum chunk size in Azure Custom Vision.
        """
        for i in range(0, len(lst), n):
            yield lst[i: i + n]

    def upload_images(self, labels: List, container_name) -> None:
        """
            Takes as input a list of labels, uploads all assosiated images to Azure Custom Vision project.
            If label in input already exists in Custom Vision project, all images are uploaded directly.
            If label in input does not exist in Custom Vision project, new label (Tag object in Custom Vision) is created before uploading images

            Parameters:
            labels (str[]): List of labels

            Returns:
            None
        """
        url_list = []
        existing_tags = list(self.trainer.get_tags(self.project_id))

        try:
            container = self.blob_service_client.get_container_client(
                container_name
            )
        except Exception as e:
            print(
                "could not find container with CONTAINER_NAME name error: ",
                str(e),
            )

        for label in labels:
            # check if input has correct type
            if not isinstance(label, str):
                raise Exception("label " + str(label) + " must be a string")

            tag = [t for t in existing_tags if t.name == label]
            # check if tag already exists
            if len(tag) == 0:
                try:
                    tag = self.trainer.create_tag(self.project_id, label)
                    print("Created new label in project: " + label)
                except Exception as e:
                    print(e)
                    continue
            else:
                tag = tag[0]

            blob_prefix = f"{label}/"
            blob_list = container.list_blobs(name_starts_with=blob_prefix)

            if not blob_list:
                raise AttributeError("no images for this label")

            # build correct URLs and append to URL list
            for blob in blob_list:
                blob_url = f"{self.base_img_url}/{container_name}/{blob.name}"
                url_list.append(
                    ImageUrlCreateEntry(url=blob_url, tag_ids=[tag.id])
                )

        # upload URLs in chunks of 64
        print("Uploading images from blob to CV")
        img_f = 0
        img_s = 0
        img_d = 0
        itr_img = 0
        chunks = self.__chunks(url_list, setup.CV_MAX_IMAGES)
        num_imgs = len(url_list)
        error_messages = set()
        for url_chunk in chunks:
            upload_result = self.trainer.create_images_from_urls(
                self.project_id, batch=ImageUrlCreateBatch(images=url_chunk)
            )
            if not upload_result.is_batch_successful:
                for image in upload_result.images:
                    if image.status == "OK":
                        img_s += 1
                    elif image.status == "OKDuplicate":
                        img_d += 1
                    else:
                        error_messages.add(image.status)
                        img_f += 1

                    itr_img += 1
            else:
                batch_size = len(upload_result.images)
                img_s += batch_size
                itr_img += batch_size

            prc = itr_img / num_imgs
            print(
                f"\t succesfull: \033[92m {img_s:5d} \033]92m \033[0m",
                f"\t duplicates: \033[33m {img_d:5d} \033]33m \033[0m",
                f"\t failed: \033[91m {img_f:5d} \033]91m \033[0m",
                f"\t [{prc:03.2%}]",
                sep="",
                end="\r",
                flush=True,
            )

        print()
        if len(error_messages) > 0:
            print("Error messages:")
            for error_message in error_messages:
                print(f"\t {error_message}")

    def get_iteration(self):
        iterations = self.trainer.get_iterations(self.project_id)
        iterations.sort(key=(lambda i: i.created))
        newest_iteration = iterations[-1]
        return newest_iteration

    def delete_iteration(self) -> None:
        """
            Deletes the oldest iteration in Custom Vision if there are 11 iterations.
            Custom Vision allows maximum 10 iterations in the free version.
        """
        iterations = self.trainer.get_iterations(self.project_id)
        if len(iterations) >= setup.CV_MAX_ITERATIONS:
            iterations.sort(key=lambda i: i.created)
            oldest_iteration = iterations[0].id
            self.trainer.unpublish_iteration(self.project_id, oldest_iteration)
            self.trainer.delete_iteration(self.project_id, oldest_iteration)

    def train(self, labels: list) -> None:
        """
            Trains model on all labels specified in input list, exeption is raised by self.trainer.train_projec() is asked to train on non existent labels.
            Generates unique iteration name, publishes model and sets self.iteration_name if successful.
            Parameters:
            labels (str[]): List of labels
        """
        try:
            email = Keys.get("EMAIL")
        except Exception:
            print("No email found, setting to empty")
            email = ""

        self.delete_iteration()
        print("Training...")
        iteration = self.trainer.train_project(
            self.project_id,
            reserved_budget_in_hours=1,
            notification_email_address=email,
        )
        # Wait for training to complete
        start = time.time()
        while iteration.status != "Completed":
            iteration = self.trainer.get_iteration(
                self.project_id, iteration.id
            )
            minutes, seconds = divmod(time.time() - start, 60)
            print(
                f"Training status: {iteration.status}",
                f"\t[{minutes:02.0f}m:{seconds:02.0f}s]",
                end="\r",
            )
            time.sleep(1)

        print()

        # The iteration is now trained. Publish it to the project endpoint
        iteration_name = uuid.uuid4()
        self.trainer.publish_iteration(
            self.project_id,
            iteration.id,
            iteration_name,
            self.prediction_resource_id,
        )
        with app.app_context():
            self.iteration_name = models.update_iteration_name(iteration_name)

    def delete_all_images(self) -> None:
        """
            Function for deleting uploaded images in Customv Vision.
        """
        try:
            self.trainer.delete_images(
                self.project_id, all_images=True, all_iterations=True
            )
        except Exception as e:
            raise Exception("Could not delete all images: " + str(e))

    def delete_all_tags(self) -> None:
        """
            Function for deleting all tags in Custom Vision.
        """
        try:
            tags = self.trainer.get_tags(self.project_id)
            for tag in tags:
                self.trainer.delete_tag(self.project_id, tag.id)
        except Exception as e:
            raise Exception("Could not delete all tags" + str(e))

    def retrain(self):
        """
            Train model on all labels and update iteration.
        """
        with app.app_context():
            labels = models.get_all_labels()

        self.upload_images(labels, setup.CONTAINER_NAME_NEW)
        try:
            self.train(labels)
        except CustomVisionErrorException as e:
            msg = "No changes since last training"
            print(e, "exiting...")
            raise excp.BadRequest(msg)

    def hard_reset_retrain(self):
        """
            Train model on all labels and update iteration.
            This method sleeps for 60 seconds to make sure all
            old images are deleted from custom vision before
            uploading original dataset.
        """
        with app.app_context():
            labels = models.get_all_labels()

        # Wait 60 seconds to make sure all images are deleted in custom vision
        time.sleep(60)
        self.upload_images(labels, setup.CONTAINER_NAME_ORIGINAL)
        try:
            self.train(labels)
        except CustomVisionErrorException as e:
            msg = "No changes since last training"
            print(e, "exiting...")
            raise excp.BadRequest(msg)

    def classify_images_by_label(self, label, number_of_examples):
        """
            Classifies images by label and returns a list of correctly classified images.
        """
        # Load the blob service client
        container_client = self.blob_service_client.get_container_client(
            setup.CONTAINER_NAME_ORIGINAL)

        blob_prefix = f"{label}/"

        # List all blobs in the container
        blobs = list(container_client.list_blobs(name_starts_with=blob_prefix))

        # List to store correctly classified images
        images = []
        for blob in blobs:
            blob_client = container_client.get_blob_client(blob)
            image_url = blob_client.url

            pred_kv, best_guess = self.predict_image_url(image_url)

            if pred_kv[best_guess] > 0.7:
                images.append(blob["name"])
            # Check if the image is classified correctly
            if len(images) >= number_of_examples:
                return images
        return images


def main():
    """
        Use main if you want to run the complete program with init, train and prediction of and example image.
        To be able to run main, make sure:
        -no more than two projects created in Azure Custom Vision
        -no more than 10 iterations done in one projectS
    """
    test_url = "https://i.imgur.com/PamZxsc.png"

    classifier = Classifier()

    # classifier.upload_images(["belt", "apple", "airplane"], "oldimgcontainer")

    # classifier.train(["belt", "apple", "airplane"])

    # classify image with URL reference
    result, best_guess = classifier.predict_image_url(test_url)
    print(f"url result:\n{best_guess} url result {result}")

    # classify image
    with open("./preprocessing/images/airplane/4554736336371712.png", "rb") as f:
        # result, best_guess = classifier.predict_image(f)
        result = classifier.predict_image_by_post(f)
        print(f"png result:\n{result}")

    # with api.app.app_context():
    #    labels = models.get_all_labels()

    # classifier.upload_images(labels, "old")
    # classifier.train(labels)


if __name__ == "__main__":
    main()
