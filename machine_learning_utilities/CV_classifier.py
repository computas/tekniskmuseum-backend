from msrest.authentication import ApiKeyCredentials
from azure.storage.blob import BlobServiceClient
from azure.cognitiveservices.vision.customvision.prediction import (
    CustomVisionPredictionClient,
)

import secrets

# from config import (
#     ENDPOINT,
#     prediction_key,
#     project_id,
#     connect_str,
# )

ENDPOINT = secrets.get("ENDPOINT")
connect_str = secrets.get("connect_str")
project_id = secrets.get("project_id")
prediction_key = secrets.get("prediction_key")


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

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    classifier = CVClassifier(blob_service_client)
    result = classifier.predict(test_url)

    print([(i.tag_name, i.probability) for i in result])


if __name__ == "__main__":
    main()
