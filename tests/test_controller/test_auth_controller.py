import base64
import functools
import json
from typing import Any, List

import pytest
import requests
from flask import Flask
from mock import MagicMock, Mock
from pytest_mock import MockFixture

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.client import activation_auth_client
from dhos_janitor_api.blueprint_api.controller import auth_controller

real_requests_get = requests.get
real_requests_post = requests.post


class TestAuthController:
    def test_get_system_jwt(self) -> None:
        first_result = auth_controller.get_system_jwt("something")
        assert not auth_controller.has_expired(first_result)

        # Second time should be cached
        second_result = auth_controller.get_system_jwt("something")
        assert second_result == first_result

    @pytest.mark.parametrize("username", ("Gregory House", ""))
    @pytest.mark.parametrize("password", ("qwerty123", ""))
    @pytest.mark.parametrize("use_auth0", (True, False))
    def test_get_clinician_jwt_errors(
        self, app: Flask, username: str, password: str, use_auth0: bool
    ) -> None:
        if not username or (not password and use_auth0):
            with pytest.raises(ValueError):
                auth_controller.get_clinician_jwt(
                    username=username, password=password, use_auth0=use_auth0
                )

    @pytest.mark.parametrize("use_auth0", (True, False))
    def test_get_clinician_jwt(self, mocker: Any, app: Flask, use_auth0: bool) -> None:
        username: str = "Gregory House"
        password: str = "qwerty123"
        scopes: List[str] = ["read:comics", "write:comics"]

        mock_get_clinician_data: Mock = mocker.patch.object(
            auth_controller,
            "_get_clinician_data",
            return_value={"groups": ["GDM Clinician"], "uuid": "dr. house"},
        )
        mock_get_permissions_for_group: Mock = mocker.patch.object(
            auth_controller, "_get_permissions_for_group", return_value=scopes
        )
        mock_auth0: Mock = mocker.patch.object(
            auth_controller.auth0_jwt,
            "get_auth0_jwt_for_user",
            return_value="jwt jwt jwt",
        )

        jwt = auth_controller.get_clinician_jwt(
            username=username, password=password, use_auth0=use_auth0
        )

        assert jwt

        if use_auth0:
            mock_get_clinician_data.assert_not_called()
            mock_get_permissions_for_group.assert_not_called()
            mock_auth0.assert_called_once()
        else:
            mock_get_clinician_data.assert_called_once_with(username, None)
            mock_get_permissions_for_group.assert_called_once_with("GDM Clinician")
            mock_auth0.assert_not_called()

    def test_patient_jwt(
        self,
        clients: ClientRepository,
        mocker: MockFixture,
        patient_id: str,
        system_jwt: str,
    ) -> None:
        mock_create_activation_for_patient = mocker.patch.object(
            activation_auth_client,
            "create_activation_for_patient",
            return_value={"activation_code": 123, "otp": 321},
        )
        mock_create_activation = mocker.patch.object(
            activation_auth_client,
            "create_activation",
            return_value={"authorisation_code": 333},
        )
        mock_get_patient_jwt = mocker.patch.object(
            activation_auth_client, "get_patient_jwt", return_value={"jwt": 111}
        )

        jwt = auth_controller.get_patient_jwt(clients, patient_id)

        mock_create_activation_for_patient.assert_called_once_with(
            clients, patient_id, system_jwt
        )
        mock_create_activation.assert_called_once_with(clients, 123, 321)
        mock_get_patient_jwt.assert_called_once_with(clients, patient_id, 333)

        assert jwt == 111

    def test_get_auth_from_b64_basic_auth(self) -> None:
        username = "test_user"
        password = "test_password"
        user_pass = f"{username}:{password}".encode("ascii")
        user_pass_b64 = base64.b64encode(user_pass).decode("ascii")
        auth_header = f"Basic {user_pass_b64}"

        auth_user, auth_pass = auth_controller.get_auth_from_b64_basic_auth(auth_header)

        assert auth_user == username
        assert auth_pass == password

    @pytest.mark.parametrize("username", ("Salmon", None))
    @pytest.mark.parametrize("clinician_uuid", ("Tuna", None))
    @pytest.mark.parametrize("exists", (True, False))
    @pytest.mark.parametrize("count", (1, 2))
    def test_get_clinician_data(
        self,
        mocker: MockFixture,
        username: str,
        clinician_uuid: str,
        exists: bool,
        count: int,
    ) -> None:
        clinicians = {
            "clinician": [
                {
                    "email_address": username if exists else "Prawn",
                    "uuid": clinician_uuid if exists else "Lobster",
                }
            ]
        }
        if count == 2:
            clinicians["clinician"].append(clinicians["clinician"][0])

        mock_data = MagicMock()
        mock_data.read_text.return_value = json.dumps(clinicians)

        mock_logger_warning = mocker.patch.object(auth_controller.logger, "warning")
        mocker.patch.object(auth_controller, "DHOS_SERVICES_DATA_PATH", new=mock_data)
        get_clinician_data = functools.partial(
            auth_controller._get_clinician_data, username, clinician_uuid
        )

        if (username is None and clinician_uuid is None) or not exists:
            with pytest.raises(ValueError):
                get_clinician_data()
        else:
            clinician_data = get_clinician_data()

            if count == 2:
                mock_logger_warning.assert_called_once()

            assert clinician_data == clinicians["clinician"][0]
