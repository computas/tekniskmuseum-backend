#!/bin/python3
"""
    This file is used for running pytests in github actions. It parses keys from github sectrets and runs tests.
    The file is called in github action with secrets as argument.
"""
import json
import os
import sys
import pytest
import argparse

# parse cli arguments
parser = argparse.ArgumentParser(description='get key string')
parser.add_argument('--keys', action='store', type=str,
                    help='The text to parse.')
arguments = parser.parse_args()


# export keys
keylist = json.loads(arguments.keys)
for keydict in keylist:
    os.environ[keydict["name"]] = keydict["value"]

# clear cli arguments as pytest reads them
sys.argv = [sys.argv[0]]

# run pytets
test_result = pytest.main()
assert test_result == 0
