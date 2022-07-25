import os
from typing import Dict

import httpx
import pytest
from mock import Mock
from pytest_mock import MockFixture
from respx import MockRouter

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.client import gdm_bff_client


@pytest.mark.usefixtures("mock_patient_jwt")
@pytest.mark.respx(base_url=os.getenv("GDM_BFF"))
class TestGDMBFFClient:
    @pytest.fixture
    def spy_make_request(self, mocker: MockFixture) -> Mock:
        return mocker.spy(gdm_bff_client, "make_request")

    def test_create_reading(
        self,
        clients: ClientRepository,
        respx_mock: MockRouter,
        spy_make_request: Mock,
        patient_id: str,
        patient_jwt: str,
    ) -> None:
        mock_create_reading = respx_mock.post(
            url=f"/gdm/v1/patient/{patient_id}/reading"
        ).mock(
            return_value=httpx.Response(
                status_code=200,
                json={},
            )
        )

        actual = gdm_bff_client.create_reading(
            clients, patient_id, patient_jwt, {"bg": "reading"}
        )
        spy_make_request.assert_called_once_with(
            client=clients.gdm_bff,
            method="post",
            url=f"/gdm/v1/patient/{patient_id}/reading",
            json={"bg": "reading"},
            headers={"Authorization": f"Bearer {patient_jwt}"},
        )

        assert mock_create_reading.called
        assert isinstance(actual, Dict)
