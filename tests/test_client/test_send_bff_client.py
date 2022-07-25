import os
from typing import Dict

import httpx
import pytest
from mock import Mock
from pytest_mock import MockFixture
from respx import MockRouter

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.client import send_bff_client


@pytest.mark.usefixtures("mock_clinician_jwt")
@pytest.mark.respx(base_url=os.getenv("SEND_BFF"))
class TestSENDBFFClient:
    @pytest.fixture
    def spy_make_request(self, mocker: MockFixture) -> Mock:
        return mocker.spy(send_bff_client, "make_request")

    def test_create_observation(
        self,
        clients: ClientRepository,
        respx_mock: MockRouter,
        spy_make_request: Mock,
        clinician_jwt: str,
    ) -> None:
        mock_create_observation = respx_mock.post(
            url="/send/v1/observation_set?suppress_obs_publish=true"
        ).mock(
            return_value=httpx.Response(
                status_code=200,
                json={},
            )
        )

        actual = send_bff_client.create_observation(clients, {}, True, clinician_jwt)
        spy_make_request.assert_called_once_with(
            client=clients.send_bff,
            method="post",
            url="/send/v1/observation_set",
            json={},
            params={"suppress_obs_publish": True},
            headers={"Authorization": f"Bearer {clinician_jwt}"},
        )

        assert mock_create_observation.called
        assert isinstance(actual, Dict)
