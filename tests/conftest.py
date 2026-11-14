import os

os.environ["SKIP_DEFAULT_APP"] = "1"  # tests build their own app via create_app()

import pytest

from app import create_app
from classes import load_catalog
from search import SearchIndex


@pytest.fixture(scope="session")
def catalog():
    return load_catalog()


@pytest.fixture(scope="session")
def index(catalog):
    return SearchIndex(catalog)


@pytest.fixture(scope="session")
def client():
    return create_app(secret_key="test-key").test_client()
