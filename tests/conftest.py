import os
import uuid
from typing import Any, Dict
from unittest import mock

import jose.jwt
import pytest
from flask import Flask

from dhos_janitor_api.blueprint_api.client import ClientRepository


@pytest.fixture(autouse=True)
def clean_caches() -> None:
    from dhos_janitor_api.blueprint_api.client import (
        medication_client,
        trustomer_client,
    )

    trustomer_client._cache.clear()
    medication_client._cache.clear()


@pytest.fixture
def app() -> Flask:
    import dhos_janitor_api.app

    os.environ["NO_PROXY"] = "*"

    return dhos_janitor_api.app.create_app(testing=True)


@pytest.fixture()
def random_uuid() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def patient_id(random_uuid: str) -> str:
    return random_uuid


@pytest.fixture
def device_id(random_uuid: str) -> str:
    return random_uuid


@pytest.fixture
def clinician_id(random_uuid: str) -> str:
    return random_uuid


@pytest.fixture
def location_id(random_uuid: str) -> str:
    return random_uuid


@pytest.fixture
def mock_system_jwt(mocker: mock.Mock) -> Any:
    from dhos_janitor_api.blueprint_api.controller import auth_controller

    dummy_jwt = jose.jwt.encode(
        {
            "metadata": {"system_id": "dhos-robot"},
            "iss": "http://localhost/",
            "aud": "https://dev.sensynehealth.com/",
            "scope": "read:gdm_clinician_auth_all",
            "exp": 9_999_999_999,
        },
        key="secret",
        algorithm="HS512",
    )

    return mocker.patch.object(
        auth_controller, "get_system_jwt", return_value=dummy_jwt
    )


@pytest.fixture
def mock_patient_jwt(mocker: mock.Mock) -> Any:
    from dhos_janitor_api.blueprint_api.controller import auth_controller

    return mocker.patch.object(auth_controller, "get_patient_jwt", return_value="")


@pytest.fixture
def mock_clinician_jwt(mocker: mock.Mock) -> Any:
    from dhos_janitor_api.blueprint_api.controller import auth_controller

    return mocker.patch.object(auth_controller, "get_clinician_jwt", return_value="")


@pytest.fixture
def clients(app: Flask) -> ClientRepository:
    return ClientRepository.from_app(app)


@pytest.fixture
def trustomer_dummy_config() -> Dict:
    return {
        "created": "2017-09-23T08:29:19.123+00:00",
        "gdm_config": {
            "use_epr_integration": True,
        },
        "uuid": "2c4f1d24-2952-4d4e-b1d1-3637e33cc161",
    }


@pytest.fixture
def system_jwt(mock_system_jwt: Any) -> str:
    from dhos_janitor_api.blueprint_api.controller import auth_controller

    return auth_controller.get_system_jwt()


@pytest.fixture
def patient_jwt(
    clients: ClientRepository, mock_patient_jwt: Any, patient_id: str
) -> str:
    from dhos_janitor_api.blueprint_api.controller import auth_controller

    return auth_controller.get_patient_jwt(clients, patient_id)


@pytest.fixture
def clinician_email() -> str:
    return "gregory@house.doctor"


@pytest.fixture
def clinician_jwt(mock_clinician_jwt: Any, clinician_email: str) -> str:
    from dhos_janitor_api.blueprint_api.controller import auth_controller

    return auth_controller.get_clinician_jwt(clinician_email)
