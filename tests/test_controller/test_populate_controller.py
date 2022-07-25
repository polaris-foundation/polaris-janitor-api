from typing import Dict, List
from unittest.mock import Mock

import pytest
from flask import Flask
from pytest_mock import MockFixture

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.controller import (
    auth_controller,
    generator_controller,
    populate_controller,
)


@pytest.mark.usefixtures("app")
class TestPopulateController:
    @pytest.fixture
    def readings_per_day(self) -> int:
        return 3

    @pytest.fixture
    def sample_patients(self, readings_per_day: int) -> List[Dict]:
        return [
            {
                "uuid": "static_patient_uuid_1",
                "record": {
                    "diagnoses": [
                        {
                            "sct_code": "11687002",
                            "readings_plan": {
                                "days_per_week_to_take_readings": 7,
                                "readings_per_day": readings_per_day,
                            },
                            "management_plan": {
                                "doses": [{"medication_id": "1234", "amount": 0.2}]
                            },
                        }
                    ]
                },
                "dh_products": [{"product_name": "GDM", "opened_date": "1970-01-01"}],
                "locations": ["static_location_uuid_L1"],
            },
            {
                "uuid": "static_patient_uuid_2",
                "record": {"diagnoses": [{"sct_code": "11687002"}]},
            },
            {
                "uuid": "static_patient_uuid_3",
                "record": {"diagnoses": [{"sct_code": "nope"}]},
            },
        ]

    @pytest.fixture
    def sample_clinicians(self) -> List[Dict]:
        return [
            {
                "uuid": "static_clinician_uuid_A",
                "email_address": "clinician@hospital.com",
                "groups": ["GDM Superclinician"],
            }
        ]

    @pytest.mark.usefixtures(
        "mock_system_jwt", "mock_clinician_jwt", "mock_patient_jwt"
    )
    @pytest.mark.parametrize("use_system_jwt", (False, True))
    @pytest.mark.parametrize("readings_per_day", [3, 7, 8])
    def test_populate_gdm_data(
        self,
        app: Flask,
        mocker: MockFixture,
        readings_per_day: int,
        sample_patients: List[Dict],
        sample_clinicians: List[Dict],
        clients: ClientRepository,
        use_system_jwt: bool,
    ) -> None:
        mock_search_patients: Mock = mocker.patch.object(
            populate_controller.services_client,
            "search_patients",
            return_value=sample_patients,
        )
        mock_get_clinicians: Mock = mocker.patch.object(
            populate_controller.users_client,
            "get_clinicians",
            return_value=sample_clinicians,
        )
        mock_populate = mocker.patch.object(
            populate_controller, "_populate_for_patient"
        )
        populate_controller.populate_gdm_data(
            clients, days=2, use_system_jwt=use_system_jwt
        )
        assert mock_search_patients.call_count == 2
        mock_get_clinicians.assert_called_once()
        assert mock_populate.call_count == len(sample_patients) * 2

    @pytest.mark.usefixtures(
        "mock_system_jwt", "mock_clinician_jwt", "mock_patient_jwt"
    )
    @pytest.mark.parametrize("use_system_jwt", (False, True))
    def test_populate_for_patient(
        self,
        clients: ClientRepository,
        mocker: MockFixture,
        sample_patients: List[Dict],
        sample_clinicians: List[Dict],
        use_system_jwt: bool,
    ) -> None:
        patient = sample_patients[0]
        clinician = sample_clinicians[0]

        mock_create_reading = mocker.patch.object(
            populate_controller.gdm_bff_client, "create_reading"
        )
        mocker.patch.object(populate_controller.messages_client, "create_message")
        mocker.patch.object(populate_controller.services_client, "update_patient")

        populate_controller._populate_for_patient(
            clients, patient, clinician, 2, use_system_jwt
        )

        mock_create_reading.assert_called()
