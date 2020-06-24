import os
import JSON
from azure.storage.blob import BlobClient

with open('./config.json') as configFile:
    keys = json.load(config_file)


blob = BlobClient.from_connection_string(conn_str=keys['CONNECTION_STRING'])
