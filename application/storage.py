"""
Tools for interacting with Azure blob storage.
"""
import os
import uuid
import secrets
from azure.storage.blob import BlobClient
import pdb


def saveImage(image, label):
    """
    Upload image to blob storage container with same name as image label.
    Image is renamed to assure unique name. Returns public URL to access image
    """
    filename = label + uuid.uuid4().hex + ".png"
    connectionString = secrets.get("BLOB_CONNECTION_STRING")
    containerName = 'new-' + label 
    baseurl = secrets.get('BASE_IMAGE_URL')
    try:
        blob = BlobClient.from_connection_string(
            conn_str=connectionString,
            container_name=containerName,
            blob_name=filename)
        blob.upload_blob(image)
    except Exception as e:
        print(e)
    url = baseurl + '/' + containerName + '/' + filename
    pdb.set_trace()
    return url
