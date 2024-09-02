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
ARGUMENTS = parser.parse_args()
# export keys
KEYLIST = json.loads(ARGUMENTS.keys)
for key, value in KEYLIST.items():
    os.environ[key] = value

# clear cli arguments as pytest reads them
sys.argv = [sys.argv[0]]
# run pytets
TEST_RESULT = pytest.main([])
assert TEST_RESULT == 0
