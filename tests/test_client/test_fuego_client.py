import os
from typing import Dict

import httpx
import pytest
from mock import Mock
from pytest_mock import MockFixture
from respx import MockRouter

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.client import fuego_client


@pytest.mark.usefixtures("mock_system_jwt")
@pytest.mark.respx(base_url=os.getenv("DHOS_FUEGO_API"))
class TestFuegoClient:
    @pytest.fixture
    def spy_make_request(self, mocker: MockFixture) -> Mock:
        return mocker.spy(fuego_client, "make_request")

    def test_create_fhir_patient(
        self,
        clients: ClientRepository,
        respx_mock: MockRouter,
        system_jwt: str,
        spy_make_request: Mock,
    ) -> None:
        mock_create_fhir_patient = respx_mock.post(url="/dhos/v1/patient_create").mock(
            return_value=httpx.Response(
                status_code=200,
                json={},
            )
        )

        actual = fuego_client.create_fhir_patient(clients, {}, system_jwt)
        spy_make_request.assert_called_once_with(
            client=clients.dhos_fuego_api,
            method="post",
            url="/dhos/v1/patient_create",
            json={},
            headers={"Authorization": f"Bearer {system_jwt}"},
        )

        assert mock_create_fhir_patient.called
        assert isinstance(actual, Dict)
