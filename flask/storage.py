'''
Tools for interacting with Azure blob storage.
'''
import json
import uuid
from azure.storage.blob import BlobClient

with open('./config.json') as configFile:
    keys = json.load(configFile)


def saveImage(image, label):
    '''
    Upload image to blob storage container with same name as image label.
    Image is renamed to assure unique name.
    '''
    filename = label + uuid.uuid4().hex + '.png'
    blob = BlobClient.from_connection_string(
        conn_str=keys['CONNECTION_STRING'],
        container_name=label,
        blob_name=filename,
        )
    blob.upload_blob(image)
