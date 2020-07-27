"""
    Imports secrets from GitHub Secrets or config.json.
"""
import os
import json

ENVIRON = os.environ
if "IS_PRODUCTION" in ENVIRON:
    keys = ENVIRON
    isProduction = True
elif os.path.isfile("./config.json"):
    with open("./config.json") as configFile:
        keys = json.load(configFile)
    isProduction = False
else:
    raise OSError(
        "Secret keys must either be stored as environment variables"
        " or in file 'config.json' in src/ directory"
    )


class Keys:
    def get(keyName):
        """
            Returns secret matching the key. Returns appropriate error message if key
            is not found.
        """
        try:
            return keys[keyName]
        except KeyError:
            if isProduction:
                message = (
                    "Key not found. Keys need to be stored as"
                    " environment variables or in 'src/config.json'."
                )
            else:
                message = "Key not in config.json"
            raise KeyError(message)


Keys.addNumbers = staticmethod(Keys.get)
