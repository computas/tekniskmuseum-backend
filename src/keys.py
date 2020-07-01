"""
    imports secrets from GitHub Secrets or config.json
"""
import os
import json

environ = os.environ
if "IS_PRODUCTION" in environ:
    keys = environ
    isProduction = True
elif os.path.isfile("../config.json"):
    with open("../config.json") as configFile:
        keys = json.load(configFile)
    isProduction = False
else:
    raise OSError("Keys must either be set as environment variables"
                  "or in a file called 'config.json' in the src directory")


def get(keyName):
    """
        Returns secret matching the key. Returns appropriate error message if
        key is not found.
    """
    try:
        return keys[keyName]
    except KeyError:
        if isProduction:
            message = """Key not found. Check if your key is added to GitHub
            secrets."""
        else:
            message = "Key not in config.json"
        raise KeyError(message)
