"""
    Tools for interacting with Azure blob storage.
"""
import os
import uuid
import sys
import time
import logging
from webapp import api
from threading import Thread
from azure.storage.blob import BlobClient
from azure.storage.blob import BlobServiceClient
from utilities.keys import Keys
from utilities import setup


def save_image(image, label, certainty):
    """
        Upload image to blob storage container named "newimgcontainer" with same name as image label.
        Image is renamed to assure unique name. Uploads only if certainty is larger than threshold
        Returns public URL to access image, or non if certainty too low.
    """
    # save image in blob storage if certainty above threshold
    if certainty < setup.SAVE_CERTAINTY:
        return

    file_name = f"{label}/{uuid.uuid4().hex}.png"
    connection_string = Keys.get("BLOB_CONNECTION_STRING")
    base_url = Keys.get("BASE_BLOB_URL")
    container_name = setup.CONTAINER_NAME_NEW
    try:
        blob = BlobClient.from_connection_string(
            conn_str=connection_string,
            container_name=container_name,
            blob_name=file_name,
        )
        blob.upload_blob(image)
        container_client = blob_connection()
        # update metadata in blob
        image_count = int(
            container_client.get_container_properties().metadata["image_count"]
        )
        metadata = {"image_count": str(image_count + 1)}
        container_client.set_container_metadata(metadata=metadata)
    except Exception as e:
        api.app.logger.error(e)
    url = base_url + "/" + container_name + "/" + file_name
    logging.info(url)
    return url


def clear_dataset():
    """
        Method for resetting dataset back to original dataset
        from Google Quickdraw. It deletes the 'New Images Container'.
        NOTE: container is deleted by garbage collection, which does not
        happen instantly. A new blob cannot be initalized before old is collected.
    """
    container_client = blob_connection()
    try:
        container_client.delete_container()
    except Exception as e:
        raise Exception("could not delete container" + str(e))
    Thread(target=create_container).start()


def create_container():
    """
        Method for creating a new container. Tries to create a new container
        n times, to make sure Azure garbage collection is finished.
    """
    tries = setup.CREATE_CONTAINER_TRIES
    waiting_time = setup.CREATE_CONTAINER_WAITER
    container_client = blob_connection()
    success = False
    metadata = {"image_count": "0"}
    for i in range(tries):
        if success:
            return

        time.sleep(waiting_time)
        try:
            container_client.create_container(
                metadata=metadata, public_access="container"
            )
            success = True
        except Exception as e:
            api.app.logger.error(e)


def image_count():
    """
        Returns number of images in 'newimgcontainer'.
    """
    container_client = blob_connection()
    return container_client.get_container_properties().metadata["image_count"]


def blob_connection():
    """
        Helper method for connection to blob service.
    """
    container_name = setup.CONTAINER_NAME_NEW
    connect_str = Keys.get("BLOB_CONNECTION_STRING")
    try:
        # Instantiate a BlobServiceClient using a connection string
        blob_service_client = BlobServiceClient.from_connection_string(
            connect_str
        )
        # Instantiate a ContainerClient
        container_client = blob_service_client.get_container_client(
            container_name
        )
    except Exception as e:
        raise Exception("Could not connect to blob client: " + str(e))

    return container_client
