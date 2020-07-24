"""
    Tools for interacting with Azure blob storage.
"""
import os
import uuid
import sys
import logging
from webapp import api
from azure.storage.blob import BlobClient
from azure.storage.blob import BlobServiceClient
from utilities.keys import Keys


def save_image(image, label):
    """
        Upload image to blob storage container with same name as image label.
        Image is renamed to assure unique name. Returns public URL to access
        image.
    """
    file_name = f"new/{label}/{uuid.uuid4().hex}.png"
    connection_string = Keys.get("BLOB_CONNECTION_STRING")
    container_name = Keys.get("CONTAINER_NAME")
    base_url = Keys.get("BASE_BLOB_URL")
    try:
        blob = BlobClient.from_connection_string(
            conn_str=connection_string,
            container_name=container_name,
            blob_name=file_name,
        )
        blob.upload_blob(image)
    except Exception as e:
        api.app.logger.error(e)

    url = base_url + "/" + container_name + "/" + file_name

    logging.info(url)

    return url


def clear_dataset():
    """
        Method for resetting dataset back to original dataset 
        from Google Quickdraw. It deletes all blobs in /oldim
    """
    container_name = Keys.get("CONTAINER_NAME")
    connect_str = Keys.get("BLOB_CONNECTION_STRING")
    # Instantiate a BlobServiceClient using a connection string
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    # Instantiate a ContainerClient
    container_client = blob_service_client.get_container_client(container_name)

    blob_prefix = "new/axe"
    blob_list = container_client.list_blobs(name_starts_with=blob_prefix)

    blob_names = [bytes(blob.name, "utf-8") for blob in blob_list]
    print(blob_names)
    container_client.delete_blobs(blob_names)

    """
    for blob in blob_list:
        print("ok")
        try:
            print("deleting: ", blob.name)
            blob_name = blob.name
            container_client.delete_blob(blob.name)
            print("was deleted")
        except Exception as e:
            raise Exception(
                "could not delete blob with name: ",
                blob.name,
                ". Error message: ",
                str(e),
            )
    """

