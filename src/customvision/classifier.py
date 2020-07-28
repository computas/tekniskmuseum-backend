#! /usr/bin/env python
"""
    Tools for interacting with Azure Custom Vision and Azure Blob Storage
"""
import uuid
import time
import sys
import os
from typing import Dict
from typing import List
from utilities.keys import Keys
from utilities import setup
from webapp import models
from webapp import api
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
)


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
        self.project_id = Keys.get("CV_PROJECT_ID")
        self.prediction_key = Keys.get("CV_PREDICTION_KEY")
        self.training_key = Keys.get("CV_TRAINING_KEY")
        self.base_img_url = Keys.get("BASE_BLOB_URL")
        self.prediction_resource_id = Keys.get("CV_PREDICTION_RESOURCE_ID")

        self.prediction_credentials = ApiKeyCredentials(
            in_headers={"Prediction-key": self.prediction_key}
        )
        self.predictor = CustomVisionPredictionClient(
            self.ENDPOINT, self.prediction_credentials
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

        # get all project iterations
        iterations = self.trainer.get_iterations(self.project_id)
        # find published iterations
        puplished_iterations = [
            iteration
            for iteration in iterations
            if iteration.publish_name != None
        ]
        # get the latest published iteration
        puplished_iterations.sort(key=lambda i: i.created)
        self.iteration_name = puplished_iterations[-1].publish_name
        with api.app.app_context():
            models.update_iteration_name(self.iteration_name)

    def predict_image_url(self, img_url: str) -> Dict[str, float]:
        """
            Predicts label(s) of Image read from URL.

            Parameters:
            img_url: Image URL

            Returns:
            (prediction (dict[str,float]): labels and assosiated probabilities,
            best_guess: (str): name of the label with highest probability)
        """
        with api.app.app_context():
            self.iteration_name = models.get_iteration_name()
        res = self.predictor.classify_image_url(
            self.project_id, self.iteration_name, img_url
        )
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
        with api.app.app_context():
            self.iteration_name = models.get_iteration_name()
        res = self.predictor.classify_image_with_no_store(
            self.project_id, self.iteration_name, img
        )
        # reset the file head such that it does not affect the state of the file handle
        img.seek(0)
        pred_kv = dict([(i.tag_name, i.probability) for i in res.predictions])
        best_guess = max(pred_kv, key=pred_kv.get)
        return pred_kv, best_guess

    def __chunks(self, lst, n):
        """
            Helper method used by upload_images() to upload URL chunks of 64, which is maximum chunk size in Azure Custom Vision.
        """
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    def upload_images(self, labels: List) -> None:
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
            container_new = self.blob_service_client.get_container_client(
                setup.CONTAINER_NAME_NEW
            )
<<<<<<< HEAD
            container_original = self.blob_service_client.get_container_client(
                setup.CONTAINER_NAME_ORIGINAL
=======
        except Exception as e:
            api.app.logger.info(
                "could not find container with CONTAINER_NAME name error: ", e,
>>>>>>> 33304d8b20984c6e4fa2484f539b0ab574e5d482
            )
        except Exception as e:
            raise Exception("could not connect to container: " + str(e))

        for label in labels:
            # check if input has correct type
            if not isinstance(label, str):
                raise Exception("label " + str(label) + " must be a string")

            tag = [t for t in existing_tags if t.name == label]
            # check if tag already exists
            if len(tag) == 0:
                try:
                    tag = self.trainer.create_tag(self.project_id, label)
                    api.app.logger.info("Created new label in project: " + label)
                except Exception as e:
                    api.app.logger.info(e)
                    continue
            else:
                tag = tag[0]

            blob_prefix = f"{label}/"
            blob_list_new = container_new.list_blobs(
                name_starts_with=blob_prefix
            )
            blob_list_original = container_original.list_blobs(
                name_starts_with=blob_prefix
            )

            # TODO do we need this if? we might want to upload anyway
            if not blob_list_new or not blob_list_original:
                raise AttributeError("no images for this label")

            # build correct URLs and append to URL list
            for blob in blob_list_new:
                blob_url = f"{self.base_img_url}/{setup.CONTAINER_NAME_NEW}/{blob.name}"
                url_list.append(
                    ImageUrlCreateEntry(url=blob_url, tag_ids=[tag.id])
                )
                print(blob.name)

            return

<<<<<<< HEAD
            for blob in blob_list_original:
                blob_url = f"{self.base_img_url}/{setup.CONTAINER_NAME_ORIGINAL}/{blob.name}"
=======
                blob_url = f"{self.base_img_url}/{Keys.get('CONTAINER_NAME')}/{blob_name}"
                # api.app.logger.info(Keys.get("CONTAINER_NAME"))
>>>>>>> 33304d8b20984c6e4fa2484f539b0ab574e5d482
                url_list.append(
                    ImageUrlCreateEntry(url=blob_url, tag_ids=[tag.id])
                )

        # upload URLs in chunks of 64
<<<<<<< HEAD
        print(f"Uploading images from blob to CV")
=======
        api.app.logger.info(f"Uploading images from '{dir_name}' to CV")
>>>>>>> 33304d8b20984c6e4fa2484f539b0ab574e5d482
        img_f = 0
        img_s = 0
        img_d = 0
        itr_img = 0
        chunks = self.__chunks(url_list, setup.CV_MAX_IMAGES)
        num_imgs = len(url_list)
        error_messages = []
        for url_chunk in chunks:
            upload_result = self.trainer.create_images_from_urls(
                self.project_id, images=url_chunk
            )
            if not upload_result.is_batch_successful:
                for image in upload_result.images:
                    if image.status == "OK":
                        img_s += 1
                    elif image.status == "OKDuplicate":
                        img_d += 1
                    else:
                        error_messages.append(image.status)
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

        api.app.logger.info()
        if len(error_messages) > 0:
            api.app.logger.info("Error messages:")
        for emsg in error_messages:
            api.app.logger.info(f"\t {emsg}")

    def getIteration(self):
        return self.trainer.get_iterations(self.project_id)[-1]

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

            then publishes the model.
            C
            Parameters:
            labels (str[]): List of labels

            Returns:
            None

            # TODO
            There might arrise an error where the self.iteration_name is not syncronised between processes.
            If the processes live long enough this will cause prediciton to fail due to the oldest iteration being deleted when training happens

            Potential fixes for this are requesting the latest iteration_name every time you predict,
            or storing the latest iteration name in a database and fetching this every time you do a prediction
        """
        try:
            email = Keys.get("EMAIL")
        except Exception:
            api.app.logger.info("No email found, setting to empty")
            email = ""

        self.delete_iteration()
        api.app.logger.info("Training...")
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
            api.app.logger.info(f"Training status: {iteration.status}",
                                f"\t[{minutes:02.0f}m:{seconds:02.0f}s]", end="\r")
            time.sleep(1)

        api.app.logger.info()

        # The iteration is now trained. Publish it to the project endpoint
        iteration_name = uuid.uuid4()
        self.trainer.publish_iteration(
            self.project_id,
            iteration.id,
            iteration_name,
            self.prediction_resource_id,
        )
        with api.app.app_context():
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

    def retrain(self):
        """
            Train model on all labels and update iteration.
        """
        with api.app.app_context():
            labels = models.get_all_labels()
        self.upload_images(labels)
        return
        try:
            self.train(labels)
        except CustomVisionErrorException as e:
            msg = "No changes since last training"
<<<<<<< HEAD
            print("exiting...")
=======
            api.app.logger.info(e, "exiting...")
>>>>>>> 33304d8b20984c6e4fa2484f539b0ab574e5d482
            raise excp.BadRequest(msg)


def main():
    """
        Use main if you want to run the complete program with init, train and prediction of and example image.
        To be able to run main, make sure:
        -no more than two projects created in Azure Custom Vision
        -no more than 10 iterations done in one projectS
    """
    test_url = "https://newdataset.blob.core.windows.net/oldimgcontainer/old/airplane/4554736336371712.png"

    classifier = Classifier()

    # classify image with URL reference
    result, best_guess = classifier.predict_image_url(test_url)
    api.app.logger.info(f"url result:\n{best_guess} url result {result}")

    # classify image
    with open("../data/cv_testfile.png", "rb") as f:
        result, best_guess = classifier.predict_image(f)
        api.app.logger.info(f"png result:\n{result}")

    with api.app.app_context():
        labels = models.get_all_labels()

    classifier.upload_images(labels, "old")
    classifier.train(labels)


if __name__ == "__main__":
    api.app.logger.info = print
    main()
