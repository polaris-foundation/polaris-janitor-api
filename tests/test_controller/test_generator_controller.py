import uuid
from datetime import datetime
from typing import Dict, List, Optional

import pytest
from pytest_mock import MockFixture

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.controller import generator_controller


@pytest.mark.usefixtures("mock_system_jwt", "mock_patient_jwt", "mock_clinician_jwt")
class TestGeneratorController:
    def test_gdm_closed_dh_product_fields(self) -> None:
        conception_dates = datetime(2018, 6, 18, 16, 29, 43, 79043)
        clinician_uuid = "123"
        closed_product = generator_controller._gdm_product_fields(
            conception_dates, clinician_uuid, True
        )
        assert closed_product["modified"] == "2019-03-25T16:29:43.079"

    @pytest.mark.parametrize(
        ("product", "clinicians"),
        (
            (
                "GDM",
                [
                    {
                        "uuid": "clinician_uuid",
                        "products": [{"product_name": "GDM"}],
                        "locations": ["location_uuid"],
                    }
                ],
            ),
            (
                "SEND",
                [
                    {
                        "uuid": "clinician_uuid",
                        "products": [{"product_name": "SEND"}],
                        "locations": ["location_uuid"],
                    }
                ],
            ),
            (
                "DBM",
                [
                    {
                        "uuid": "clinician_uuid",
                        "products": [{"product_name": "DBM"}],
                        "locations": ["location_uuid"],
                    }
                ],
            ),
        ),
    )
    @pytest.mark.parametrize("closed", (True, False))
    @pytest.mark.parametrize("patient_id", (None, "patient_uuid"))
    def test_generate_patients(
        self,
        clients: ClientRepository,
        mocker: MockFixture,
        product: str,
        clinicians: List[Dict],
        closed: bool,
        patient_id: Optional[str],
    ) -> None:
        mock_get_clinicians = mocker.patch.object(
            generator_controller.users_client,
            "get_clinicians",
            return_value=clinicians,
        )
        mock_get_trustomer = mocker.patch.object(
            generator_controller.trustomer_client,
            "get_trustomer_config",
            return_value={
                "uuid": str(uuid.uuid4()),
                "created": datetime.utcnow().astimezone().isoformat(),
                "gdm_config": {"medication_tags": "gdm-uk-default"},
                "dbm_config": {"medication_tags": "dbm-uk-default"},
            },
        )
        mock_get_medications = mocker.patch.object(
            generator_controller.medication_client,
            "get_medications",
            return_value=[
                {
                    "name": "Humalog Mix50",
                    "sct_code": "9512801000001102",
                    "unit": "units",
                    "uuid": "ed870a96-23df-4177-bb0c-575db80caf6f",
                }
            ],
        )

        spy_generate_diabetes_record = mocker.spy(
            generator_controller.patient_data, "generate_diabetes_record"
        )
        spy_generate_send_record = mocker.spy(
            generator_controller.patient_data, "generate_send_record"
        )

        patient = generator_controller.generate_patient(
            clients=clients, product_name=product, closed=closed, uuid=patient_id
        )

        mock_get_clinicians.assert_called_once()
        if product in ("GDM", "DBM"):
            mock_get_trustomer.assert_called_once()
            mock_get_medications.assert_called_once()
            spy_generate_diabetes_record.assert_called_once()
            spy_generate_send_record.assert_not_called()
        elif product == "SEND":
            mock_get_trustomer.assert_not_called()
            mock_get_medications.assert_not_called()
            spy_generate_diabetes_record.assert_not_called()
            spy_generate_send_record.assert_called_once()

        if patient_id:
            assert patient["uuid"] == patient_id

        for p in patient["dh_products"]:
            if product == "GDM":
                assert p["product_name"] in ("GDM", "DBM")
            else:
                assert p["product_name"] == product

            if closed and p["product_name"] == "GDM":
                assert "closed_date" in p

    def test_generate_fhir_patient(self) -> None:
        patient = generator_controller.generate_fhir_patient()
        assert "mrn" in patient
        assert "first_name" in patient
        assert "last_name" in patient
        assert "date_of_birth" in patient

    def test_generate_fhir_patient_from_dhos_services_patient(self) -> None:
        patient = {
            "hospital_number": 123,
            "first_name": "Arnold",
            "last_name": "Schwarzenegger",
            "dob": "30-07-1947",
        }

        fhir_patient = (
            generator_controller.generate_fhir_patient_from_dhos_services_patient(
                patient
            )
        )
        assert fhir_patient["mrn"] == patient["hospital_number"]
        assert fhir_patient["first_name"] == patient["first_name"]
        assert fhir_patient["last_name"] == patient["last_name"]
        assert fhir_patient["date_of_birth"] == patient["dob"]
