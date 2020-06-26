"""
Tools for interacting with Azure blob storage.
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
import keys
from azure.storage.blob import BlobClient


def saveImage(image, label):
    """
    Upload image to blob storage container with same name as image label.
    Image is renamed to assure unique name.
    """
    filename = label + uuid.uuid4().hex + ".png"
    connectionString = secrets.get("BLOB_CONNECTION_STRING")
    try:
        blob = BlobClient.from_connection_string(
            conn_str=connectionString,
            container_name=label,
            blob_name=filename,
        )
        blob.upload_blob(image)
    except Exception as e:
        print(e)
    return
