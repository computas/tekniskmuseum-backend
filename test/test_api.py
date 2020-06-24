import os, tempfile, sys
import pytest
sys.path.insert(1, '../flask')

import api

@pytest.fixture
def client():
    """
        Pytest fixture which configures application for testing.
    """
    api.app.config['TESTING'] = True
    with api.app.test_client() as client:
        yield client
