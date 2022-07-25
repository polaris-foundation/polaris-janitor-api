import datetime
import os
from typing import Dict, List

import httpx
import pytest
from flask_batteries_included.helpers.timestamp import parse_datetime_to_iso8601
from mock import Mock
from pytest_mock import MockFixture
from respx import MockRouter

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.client import encounters_client


@pytest.mark.usefixtures("mock_patient_jwt", "mock_system_jwt")
@pytest.mark.respx(base_url=os.getenv("DHOS_ENCOUNTERS_API"))
class TestEncountersClient:
    @pytest.fixture
    def spy_make_request(self, mocker: MockFixture) -> Mock:
        return mocker.spy(encounters_client, "make_request")

    def test_get_encounters_for_patient(
        self,
        clients: ClientRepository,
        respx_mock: MockRouter,
        system_jwt: str,
        spy_make_request: Mock,
        patient_id: str,
    ) -> None:
        mock_get_encounters_for_patient = respx_mock.get(url="/dhos/v2/encounter").mock(
            return_value=httpx.Response(
                status_code=200,
                json=[{}],
            )
        )

        actual = encounters_client.get_encounters_for_patient(
            clients, patient_id, system_jwt
        )
        spy_make_request.assert_called_once_with(
            client=clients.dhos_encounters_api,
            method="get",
            url="/dhos/v2/encounter",
            params={"patient_id": patient_id},
            headers={"Authorization": f"Bearer {system_jwt}"},
        )

        assert mock_get_encounters_for_patient.called
        assert isinstance(actual, List)

    def test_create_encounter(
        self,
        clients: ClientRepository,
        respx_mock: MockRouter,
        spy_make_request: Mock,
        clinician_jwt: str,
    ) -> None:
        mock_create_encounter = respx_mock.post(url="/dhos/v2/encounter").mock(
            return_value=httpx.Response(
                status_code=200,
                json={},
            )
        )

        actual = encounters_client.create_encounter(clients, {}, clinician_jwt)
        spy_make_request.assert_called_once_with(
            client=clients.dhos_encounters_api,
            method="post",
            url="/dhos/v2/encounter",
            json={},
            headers={"Authorization": f"Bearer {clinician_jwt}"},
        )

        assert mock_create_encounter.called
        assert isinstance(actual, Dict)

    def test_update_spo2_scale(
        self,
        clients: ClientRepository,
        respx_mock: MockRouter,
        spy_make_request: Mock,
        clinician_jwt: str,
    ) -> None:
        encounter_id = "1"
        mock_update_spo2_scale = respx_mock.patch(
            url=f"/dhos/v1/encounter/{encounter_id}"
        ).mock(
            return_value=httpx.Response(
                status_code=200,
                json={"score_system_history": [{}]},
            )
        )

        actual = encounters_client.update_spo2_scale(
            clients, encounter_id, 0, clinician_jwt
        )
        spy_make_request.assert_called_once_with(
            client=clients.dhos_encounters_api,
            method="patch",
            url=f"/dhos/v1/encounter/{encounter_id}",
            json={"spo2_scale": 0},
            headers={"Authorization": f"Bearer {clinician_jwt}"},
        )

        assert mock_update_spo2_scale.called
        assert isinstance(actual, Dict)

    def test_update_spo2_history(
        self,
        clients: ClientRepository,
        respx_mock: MockRouter,
        system_jwt: str,
        spy_make_request: Mock,
    ) -> None:
        score_system_history_id = "1"
        mock_update_spo2_history = respx_mock.patch(
            url=f"/dhos/v1/score_system_history/{score_system_history_id}"
        ).mock(
            return_value=httpx.Response(
                status_code=200,
            )
        )
        dt = datetime.datetime.now()
        actual = encounters_client.update_spo2_history(
            clients,
            score_system_history_id,
            dt,
            system_jwt,
        )
        spy_make_request.assert_called_once_with(
            client=clients.dhos_encounters_api,
            method="patch",
            url=f"/dhos/v1/score_system_history/{score_system_history_id}",
            json={
                "changed_time": parse_datetime_to_iso8601(
                    dt.replace(tzinfo=datetime.timezone.utc)
                )
            },
            headers={"Authorization": f"Bearer {system_jwt}"},
        )

        assert mock_update_spo2_history.called
        assert isinstance(actual, datetime.datetime)
        assert actual == dt
