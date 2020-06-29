"""
    Tools for interacting with Azure blob storage.
"""
import os
import uuid
import sys
from azure.storage.blob import BlobClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import keys  # noqa: E402


def saveImage(image, label):
    """
        Upload image to blob storage container with same name as image label.
        Image is renamed to assure unique name. Returns public URL to access
        image.
    """
    filename = label + uuid.uuid4().hex + ".png"
    connectionString = keys.get("BLOB_CONNECTION_STRING")
    containerName = "new-" + label
    baseurl = keys.get("BASE_IMAGE_URL")
    try:
        blob = BlobClient.from_connection_string(
            conn_str=connectionString,
            container_name=containerName,
            blob_name=filename)
        blob.upload_blob(image)
    except Exception as e:
        print(e)
    url = baseurl + "/" + containerName + "/r" + filename
    return url
