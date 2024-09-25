"""
    This file contains the Quick start tutorial of Custom Vision python SDK provided from Microsoft.
    Link to tutorial: https://docs.microsoft.com/en-us/azure/cognitive-services/custom-vision-service/quickstarts/image-classification?pivots=programming-language-python
"""

from azure.cognitiveservices.vision.customvision.training import (
    CustomVisionTrainingClient,
)
from azure.cognitiveservices.vision.customvision.training.models import (
    ImageUrlCreateEntry,
)
from azure.cognitiveservices.vision.customvision.prediction import (
    CustomVisionPredictionClient,
)
from msrest.authentication import ApiKeyCredentials
from azure.storage.blob import BlobServiceClient
import time
from config import (
    ENDPOINT,
    training_key,
    prediction_key,
    prediction_resource_id,
    connect_str,
)


def chunks(lst, n):
    """
        Yield successive n-sized chunks from lst.
    """
    for i in range(0, len(lst), n):
        yield lst[i: i + n]


publish_iteration_name = "drawings"

credentials = ApiKeyCredentials(in_headers={"Training-key": training_key})
trainer = CustomVisionTrainingClient(ENDPOINT, credentials)


# print(connect_str)
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

base_image_url = "https://originaldataset.blob.core.windows.net/"


# print(list(blob_service_client.list_containers()))
ambulance_container = blob_service_client.get_container_client("ambulance")
bench_container = blob_service_client.get_container_client("bench")

# Create a new project
print("Creating project...")
project = trainer.create_project("drawings")

# Make two tags in the new project
bench_tag = trainer.create_tag(project.id, "bench")
ambulance_tag = trainer.create_tag(project.id, "ambulance")
print(ambulance_tag.id)


print("Adding images...")
url_list = []

for blob in ambulance_container.list_blobs():
    blob_name = blob.name
    blob_url = f"{base_image_url}ambulance/{blob_name}"
    url_list.append(
        ImageUrlCreateEntry(url=blob_url, tag_ids=[ambulance_tag.id])
    )


for blob in bench_container.list_blobs():
    blob_name = blob.name
    blob_url = f"{base_image_url}bench/{blob_name}"
    url_list.append(ImageUrlCreateEntry(url=blob_url, tag_ids=[bench_tag.id]))


for url_chunk in chunks(url_list, 64):
    upload_result = trainer.create_images_from_urls(
        project.id, images=url_chunk
    )
    if not upload_result.is_batch_successful:
        print("Image batch upload failed.")
        for image in upload_result.images:
            if image.status != "OKDUPLICATE":
                print(image.source_url)
                print(image)
                print("Image status: ", image.status)

        nfailed = len([i for i in upload_result.images if i.status != "OK"])


print("Training...")

iteration = trainer.train_project(project.id)
while iteration.status != "Completed":
    iteration = trainer.get_iteration(project.id, iteration.id)
    print("Training status: " + iteration.status)
    time.sleep(1)

# The iteration is now trained. Publish it to the project endpoint
trainer.publish_iteration(
    project.id, iteration.id, publish_iteration_name, prediction_resource_id
)
print("Done!")
liste = trainer.get_iterations(project.id)
print(liste[0].status)


# Now there is a trained endpoint that can be used to make a prediction
prediction_credentials = ApiKeyCredentials(
    in_headers={"Prediction-key": prediction_key}
)
predictor = CustomVisionPredictionClient(ENDPOINT, prediction_credentials)

test_image_url = "https://originaldataset.blob.core.windows.net/ambulance/4504435055132672.png"

results = predictor.classify_image_url(
    project.id, publish_iteration_name, test_image_url
)

# Display the results.
for prediction in results.predictions:
    print(
        "\t"
        + prediction.tag_name
        + ": {0:.2f}%".format(prediction.probability * 100)
    )
