"""
    Imports secrets from GitHub Secrets or config.json.
"""

import os
import json
import sys

current_directory = os.path.dirname(os.path.abspath(__file__))
src_directory = os.path.dirname(current_directory)
config_file = os.path.join(src_directory, "config.json")

ENVIRON = os.environ
if "IS_PRODUCTION" in ENVIRON or "TESTING" in ENVIRON:
    keys = ENVIRON
elif os.path.isfile(config_file):
    with open(config_file) as configFile:
        keys = json.load(configFile)
    keys["IS_PRODUCTION"] = "false"
else:
    raise OSError(
        "Secret keys must either be stored as environment variables"
        " or in file 'config.json' in src/ directory"
    )


class Keys:
    def exists(keyName):
        if keyName in keys:
            return True
        else:
            return False

    def get(keyName):
        """
        Returns secret matching the key. Returns appropriate error message if key
        is not found.
        """
        try:
            return keys[keyName]
        except KeyError:
            if keys["IS_PRODUCTION"] == "true":
                message = (
                    "Key not found. Keys need to be stored as"
                    " environment variables or in 'src/config.json'."
                )
            else:
                message = f"Key not in config.json: '{keyName}'"
            raise KeyError(message)


Keys.addNumbers = staticmethod(Keys.get)
