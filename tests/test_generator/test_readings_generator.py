import random
from typing import Dict

import draymed
import pytest

from dhos_janitor_api.blueprint_api.generator.readings_generator import (
    COMMENT_LIST,
    ReadingsGenerator,
)

EDUCATION_LEVELS = [e for e in draymed.codes.list_category("education_level")]


@pytest.fixture
def sample_patient(product_name: str) -> Dict:
    return {
        "accessibility_considerations": [],
        "allowed_to_text": True,
        "created": "2018-04-05T12:42:21.096Z",
        "created_by": "testuuid",
        "dh_products": [
            {
                "accessibility_discussed": True,
                "accessibility_discussed_date": "2018-05-01",
                "accessibility_discussed_with": "D",
                "created": "2018-05-01T12:42:21.096Z",
                "created_by": "testuuid",
                "modified": "2018-05-01T12:42:21.096Z",
                "modified_by": "testuuid",
                "opened_date": "2018-05-01",
                "product_name": product_name,
            }
        ],
        "dob": "1999-10-01",
        "email_address": "Freya@email.com",
        "ethnicity": "18167009",
        "first_name": "Freya",
        "highest_education_level": random.choice(EDUCATION_LEVELS),
        "hospital_number": "ecgjndhefff",
        "last_name": "Kumar",
        "locations": [
            [
                {"display_name": "The Hospital", "uuid": "L2"},
                {"display_name": "Other Hospital", "uuid": "L1"},
            ]
        ],
        "modified": "2018-04-05T12:42:21.096Z",
        "modified_by": "testuuid",
        "nhs_number": "6666666666",
        "other_notes": "",
        "personal_addresses": [
            {
                "address_line_1": "185 Mill Byway",
                "address_line_2": "",
                "address_line_3": "",
                "address_line_4": "",
                "lived_from": "2013-05-23",
                "locality": "Putney",
                "postcode": "SW3 3YO",
                "region": "Wandsworth",
            }
        ],
        "phone_number": "07123456789",
        "record": {
            "created": "2018-05-01T12:42:21.096Z",
            "created_by": "testuuid",
            "diagnoses": [
                {
                    "created": "2018-05-01T12:42:21.096Z",
                    "created_by": "testuuid",
                    "diagnosed": "2018-05-01",
                    "diagnosis_tool": ["D0000014"],
                    "diagnosis_tool_other": "D0000018",
                    "episode": 1,
                    "management_plan": {
                        "actions": [{"action_sct_code": "12345"}],
                        "doses": [
                            {
                                "dose_amount": 1.5,
                                "medication_id": "D00123456",
                                "routine_sct_code": "1751000175104",
                            }
                        ],
                        "end_date": "2018-12-27",
                        "sct_code": "67866001",
                        "start_date": "2018-05-01",
                    },
                    "modified": "2018-05-01T12:42:21.096Z",
                    "modified_by": "testuuid",
                    "observable_entities": [
                        {
                            "date_observed": "2018-05-01",
                            "sct_code": "997671000000106",
                            "value_as_string": "A " "value",
                        }
                    ],
                    "presented": "2018-05-01",
                    "readings_plan": {
                        "days_per_week_to_take_readings": 7,
                        "end_date": "2018-12-27",
                        "readings_per_day": 4,
                        "sct_code": "54321",
                        "start_date": "2018-05-01",
                    },
                    "risk_factors": ["162864005"],
                    "sct_code": "11687002",
                }
            ],
            "history": {"gravidity": 1, "parity": 1},
            "modified": "2018-05-01T12:42:21.096Z",
            "modified_by": "testuuid",
            "notes": [],
            "pregnancies": [
                {
                    "colostrum_harvesting": True,
                    "created": "2018-05-01T12:42:21.096Z",
                    "created_by": "testuuid",
                    "deliveries": [],
                    "estimated_delivery_date": "2018-12-27",
                    "expected_number_of_babies": 2,
                    "height_at_booking_in_mm": 1528,
                    "length_of_postnatal_stay_in_days": 4,
                    "modified": "2018-05-01T12:42:21.096Z",
                    "modified_by": "testuuid",
                    "planned_delivery_place": "99b1668c-26f1-4aec-88ca-597d3a20d977",
                    "pregnancy_complications": ["47821001"],
                    "weight_at_36_weeks_in_g": 65673,
                    "weight_at_booking_in_g": 59703,
                    "weight_at_diagnosis_in_g": 54276,
                }
            ],
            "visits": [
                {
                    "clinician": "D",
                    "created": "2018-03-22T12:42:21.096Z",
                    "created_by": "D",
                    "diagnoses": [],
                    "location": "L2",
                    "modified": "2018-03-22T12:42:21.096Z",
                    "modified_by": "D",
                    "summary": "Talked about symptoms",
                    "visit_date": "2018-03-22T12:42:21.096Z",
                }
            ],
        },
        "sex": "248152002",
    }


@pytest.mark.usefixtures("app")
class TestReadingGenerator:
    def test_generate_data_without_patient(self) -> None:
        generator = ReadingsGenerator(patient=None)
        with pytest.raises(ValueError):
            generator.generate_data()

    @pytest.mark.parametrize(
        "product_name",
        ["GDM", "DBM"],
    )
    def test_generate_data_result_type(
        self, product_name: str, sample_patient: Dict
    ) -> None:
        generator = ReadingsGenerator(patient=sample_patient)
        result = generator.generate_data()
        assert isinstance(result, list)

    def test_comments(self) -> None:
        result = ReadingsGenerator.generate_comment()
        assert result in COMMENT_LIST
