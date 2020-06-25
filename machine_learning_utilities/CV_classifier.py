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

import secrets


ENDPOINT = secrets.get("ENDPOINT")
connect_str = secrets.get("connect_str")
project_id = secrets.get("project_id")
prediction_key = secrets.get("prediction_key")
training_key = secrets.get("training_key")
base_img_url = secrets.get("base_img_url")
prediction_resource_id = secrets.get("prediction_resource_id")


class CVClassifier:
    def __init__(self, blob_service_client):
        self.prediction_credentials = ApiKeyCredentials(
            in_headers={"Prediction-key": prediction_key}
        )
        self.predictor = CustomVisionPredictionClient(
            ENDPOINT, self.prediction_credentials
        )
        self.training_credentials = ApiKeyCredentials(
            in_headers={"Training-key": training_key}
        )
        self.trainer = CustomVisionTrainingClient(
            ENDPOINT, self.training_credentials
        )
        self.blob_service_client
        iterations = self.trainer.get_iterations(project_id)
        iterations.sort(key=lambda i: i.created)
        print(iterations)
        self.iteration_name = iterations[-1].publish_name

    def predict(self, img_url):
        res = self.predictor.classify_image_url(
            project_id, self.iteration_name, img_url
        )
        return res.predictions

    def __chunks(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    def upload_images(self, labels: list):
        url_list = []
        existing_tags = self.trainer.get_tags(project_id)

        # create list of URLs to be uploaded
        for label in labels:

            # check if input has correct type
            if not isinstance(label, str):
                print("label " + str(label) + " must be a string")
                return

            tag = [t for t in existing_tags if t.name == label]

            # check if tag already exists
            if len(tag) == 0:

                try:
                    tag = self.trainer.create_tag(project_id, label)
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
                blob_url = f"{base_img_url}/{label}/{blob_name}"
                url_list.append(
                    ImageUrlCreateEntry(url=blob_url, tag_ids=[tag.id])
                )

        # upload URLs in chunks of 64
        for url_chunk in self.__chunks(url_list, 64):
            upload_result = self.trainer.create_images_from_urls(
                project_id, images=url_chunk
            )
            if not upload_result.is_batch_successful:
                print("Image batch upload failed.")
                for image in upload_result.images:
                    if image.status != "OK":
                        # TODO what do we want to print here?
                        print(image.source_url)
                        # print(image)
                        print("Image status: ", image.status)

                    # nfailed = len([i for i in upload_result.images if i.status != "OK"])

    def train(self, labels: list):
        email = "mahbx@computas.com"
        emailNotify = False

        iteration_name = uuid.uuid4()
        # convert list of labels to list of tags
        # existing_tags = self.trainer.get_tags(project_id)
        # training_tags = [t for t in existing_tags if t.name in labels]

        iteration = None

        if emailNotify:
            iteration = self.trainer.train_project(
                project_id,
                reserved_budget_in_hours=1,
                notification_email_address=email,
                selected_tags=labels,
            )

        else:
            iteration = self.trainer.train_project(
                project_id, reserved_budget_in_hours=1,  # selected_tags=labels
            )

        while iteration.status != "Completed":
            iteration = self.trainer.get_iteration(project_id, iteration.id)
            print("Training status: " + iteration.status)
            time.sleep(1)

        # The iteration is now trained. Publish it to the project endpoint
        self.trainer.publish_iteration(
            project_id, iteration.id, iteration_name, prediction_resource_id
        )
        self.iteration_name = iteration_name


def main():
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    test_url = "https://originaldataset.blob.core.windows.net/ambulance/4504435055132672.png"
    labels = ["ambulance", "bench", "circle", "drawings", "square"]
    classifier = CVClassifier(blob_service_client)
    classifier.upload_images(labels)

    print("training")
    classifier.train(labels)
    result = classifier.predict(test_url)

    print([(i.tag_name, i.probability) for i in result])


if __name__ == "__main__":
    main()
