"""
    Tools for interacting with Azure blob storage.
"""
import os
import uuid
import sys
from webapp import api
from azure.storage.blob import BlobClient
from utilities.keys import Keys
import logging


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
