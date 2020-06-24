from azure.cognitiveservices.vision.customvision.training import (
    CustomVisionTrainingClient,
)
from azure.cognitiveservices.vision.customvision.training.models import (
    ImageFileCreateEntry,
    ImageUrlCreateEntry,
)
from msrest.authentication import ApiKeyCredentials
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.cognitiveservices.vision.customvision.prediction import (
    CustomVisionPredictionClient,
)
from msrest.authentication import ApiKeyCredentials
import os
from config import (
    ENDPOINT,
    training_key,
    prediction_key,
    prediction_resource_id,
    project_id,
    connect_str,
    base_img_url,
)


# print(connect_str)
blob_service_client = BlobServiceClient.from_connection_string(connect_str)


class CVClassifier:
    def __init__(self, blob_service_client):
        self.iteration_name = "drawings"
        self.prediction_credentials = ApiKeyCredentials(
            in_headers={"Prediction-key": prediction_key}
        )
        self.predictor = CustomVisionPredictionClient(
            ENDPOINT, self.prediction_credentials
        )

    def predict(self, url):
        res = self.predictor.classify_image_url(project_id, self.iteration_name, url)
        return res.predictions

    def train(self):
        pass


def main():
    test_url = (
        "https://originaldataset.blob.core.windows.net/ambulance/4504435055132672.png"
    )
    classifier = CVClassifier(blob_service_client)
    result = classifier.predict(test_url)

    print([(i.tag_name, i.probability) for i in result])


if __name__ == "__main__":
    main()
