import dataclasses
import os
from typing import Any, Generator

import pytest
import sqlalchemy
from db import metadata
from fastapi.testclient import TestClient
from main import app
from settings import DATABASE_URL, TEST_HOST, TESTS_ROOT


@dataclasses.dataclass
class Cache:
    headers = {"Authorization": "Bearer"}
    headers_other = {"Authorization": "Bearer"}
    refresh_token = {"refresh_token": ""}


@pytest.fixture(autouse=True, scope="session")
def create_test_database() -> Generator:
    """ We create tables. """
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.fixture
def client() -> Generator:
    """ We connect to the database. """
    with TestClient(app) as client:
        yield client


@pytest.fixture
def host(mocker: Any) -> Any:
    """ Set request.client.host. """
    mock_client = mocker.patch("fastapi.Request.client")
    mock_client.host = TEST_HOST
    return mock_client


@pytest.fixture
def user_one() -> dict:
    return {
        "username": "fakefive",
        "firstname": "fakefive",
        "lastname": "fakefive",
        "image": "",
        "phone": "89515200611",
        "email": "fakefive@fake.fake",
        "password": "fakefive",
    }


@pytest.fixture
def user_other() -> dict:
    return {
        "username": "fakeother",
        "firstname": "fakeother",
        "lastname": "fakeother",
        "image": "",
        "phone": "89515200612",
        "email": "fakeother@fake.fake",
        "password": "fakeother",
    }


@pytest.fixture
def user_validator() -> dict:
    return {
        "username": "fake_error",
        "firstname": "fake_error",
        "lastname": "fake_error",
        "image": "",
        "phone": "89515200613",
        "email": "fake_error@fake.fake",
        "password": "fake_error",
    }


@pytest.fixture
def email_exists() -> dict:
    return {
        "username": "unique",
        "firstname": "unique",
        "lastname": "unique",
        "image": "",
        "phone": "89515200612",
        "email": "fakeother@fake.fake",
        "password": "unique",
    }


@pytest.fixture
def username_exists() -> dict:
    return {
        "username": "fakeother",
        "firstname": "unique",
        "lastname": "unique",
        "image": "",
        "phone": "89515200612",
        "email": "unique@fake.fake",
        "password": "unique",
    }


@pytest.fixture
def image() -> str:
    with open(os.path.join(TESTS_ROOT, "imageBase64.txt")) as f:
        return f.readline()


@pytest.fixture
def room() -> dict:
    return {"name": "room", "privat": False}


@pytest.fixture
def room_privat() -> dict:
    return {"name": "room_privat", "privat": True}
