#!/bin/python3
import json
import os
import pytest
import argparse

# parse cli arguments
parser = argparse.ArgumentParser(description='get key string')
parser.add_argument('--keys', action='store', type=str,
                    help='The text to parse.')
jsonstring = parser.parse_args()

# export keys
keylist = json.reads(jsonstring)
for keydict in keylist:
    os.environ[keydict.name] = keydict.key

# run pytets
pytest.main()
