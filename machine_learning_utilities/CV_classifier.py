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
)
import uuid
import time

import sys
import os

from typing import Dict, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import keys  # noqa: e402


class CVClassifier:

    def __init__(self, blob_service_client: BlobServiceClient) -> None:
        """
            Reads configuration file
            Initializes connection to Azure Custom Vision predictor and training resources.

            Parameters:
            blob_service_client: Azure Blob Service interaction client

            Returns:
            None
        """

        self.ENDPOINT = keys.get("ENDPOINT")
        self.project_id = keys.get("PROJECT_ID")
        self.prediction_key = keys.get("PREDICTION_KEY")
        self.training_key = keys.get("TRAINING_KEY")
        self.base_img_url = keys.get("BASE_IMG_URL")
        self.prediction_resource_id = keys.get("PREDICTION_RESOURCE_ID")

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
        self.blob_service_client = blob_service_client
        iterations = self.trainer.get_iterations(self.project_id)
        iterations.sort(key=lambda i: i.created)
        self.iteration_name = iterations[-1].publish_name

    def predict_url(self, img_url: str) -> Dict[str, float]:
        """
            Predicts label(s) of Image read from URL.

            Parameters:
            img_url: Image URL

            Returns:
            prediction (dict[str,float]): labels and assosiated probabilities
        """

        res = self.predictor.classify_image_url(
            self.project_id, self.iteration_name, img_url
        )

        pred_kv = dict([(i.tag_name, i.probability) for i in res.predictions])

        return pred_kv

    def predict_png(self, png_img) -> Dict[str, float]:
        """
            Predicts label(s) of Image read from URL.
            ASSUMES:
            -image of type .png
            -image size less than 4MB
            -image resolution at least 256x256 pixels

            Parameters:
            img_url: .png file

            Returns:
            prediction (dict[str,float]): labels and assosiated probabilities
        """

        res = self.predictor.classify_image(
            self.project_id, self.iteration_name, png_img
        )

        pred_kv = dict([(i.tag_name, i.probability) for i in res.predictions])

        return pred_kv

    def __chunks(self, lst, n):
        """
            Helper method used by upload_images() to upload URL chunks of 64, which is maximum chunk size in Azure Custom Vision.
        """
        for i in range(0, len(lst), n):
            yield lst[i: i + n]

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
        existing_tags = self.trainer.get_tags(self.project_id)

        # create list of URLs to be uploaded
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

            try:
                container = self.blob_service_client.get_container_client(
                    str(label)
                )
            except Exception as e:
                print(
                    "could not find container with label "
                    + label
                    + " error: ",
                    e,
                )

            for blob in container.list_blobs():
                blob_name = blob.name
                blob_url = f"{self.base_img_url}/{label}/{blob_name}"
                url_list.append(
                    ImageUrlCreateEntry(url=blob_url, tag_ids=[tag.id])
                )

        # upload URLs in chunks of 64
        for url_chunk in self.__chunks(url_list, 64):
            upload_result = self.trainer.create_images_from_urls(
                self.project_id, images=url_chunk
            )
            if not upload_result.is_batch_successful:
                print("Image batch upload failed.")
                for image in upload_result.images:
                    if image.status != "OK":
                        print("Image status: ", image.status)

    def delete_iteration(self) -> None:
        """
            Deletes the oldest iteration in Custom Vision if there are 11 iterations. 
            Custom Vision allows maximum 10 iterations in the free version. 
        """

        iterations = self.trainer.get_iterations(self.project_id)

        if len(iterations) >= 10:

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

        email = None

        self.delete_iteration()

        print("Training...")
        iteration = self.trainer.train_project(
            self.project_id,
            reserved_budget_in_hours=1,
            notification_email_address=email,
        )

        # Wait for training to complete
        while iteration.status != "Completed":
            iteration = self.trainer.get_iteration(
                self.project_id, iteration.id)
            print("Training status: " + iteration.status)
            time.sleep(1)

        # The iteration is now trained. Publish it to the project endpoint
        iteration_name = uuid.uuid4()

        self.trainer.publish_iteration(
            self.project_id, iteration.id, iteration_name, self.prediction_resource_id
        )
        self.iteration_name = iteration_name


def main():
    """
        Use main if you want to run the complete program with init, train and prediction of and example image.
        To be able to run main, make sure:
        -no more than two projects created in Azure Custom Vision
        -no more than 11 iterations done in one projectS
    """

    connect_str = keys.get("CONNECT_STR")

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    test_url = "https://originaldataset.blob.core.windows.net/ambulance/4504435055132672.png"

    labels = ["ambulance", "bench", "circle", "star", "square"]
    classifier = CVClassifier(blob_service_client)
    # classifier.upload_images(labels)

    # classifier.train(labels)

    with open("machine_learning_utilities/test_data/4504435055132672.png", "rb") as f:

        result = classifier.predict_png(f)

    print(f"png result {result}")

    result = classifier.predict_url(test_url)

    print(f"url result {result}")


if __name__ == "__main__":
    main()
