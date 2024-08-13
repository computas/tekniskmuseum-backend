import pytest
from webapp.api import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            pass
        yield client
