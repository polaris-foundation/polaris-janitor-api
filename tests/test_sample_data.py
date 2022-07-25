from datetime import datetime, timezone
from typing import Dict, List

import pytest

from dhos_janitor_api.data import patient_data


@pytest.mark.usefixtures("app")
class TestSampleData:
    def test_record(self, sample_medications: List[Dict[str, str]]) -> None:
        conception_date = datetime(2018, 6, 18, 16, 29, 43, 79043)
        record = patient_data.generate_diabetes_record(
            "D",
            conception_date=conception_date,
            medications=sample_medications,
            closed=True,
        )
        assert record["created_by"] == "D"

    def test_convert_time(self) -> None:
        dated = datetime(2018, 6, 18, 16, 29, 43, 79043)
        conversion = patient_data.convert_time(dated)
        assert conversion == datetime(
            2018, 6, 18, 16, 29, 43, 79043, tzinfo=timezone.utc
        )

    def test_pregnancy_date(self) -> None:
        conception = datetime(2018, 6, 18, 16, 29, 43, 79043)
        pregnancy = patient_data.pregnancy_dates(conception)
        assert pregnancy["conception_timing"] == datetime(
            2018, 6, 18, 16, 29, 43, 79043
        )
        assert pregnancy["presented_date"] == datetime(2018, 7, 8, 16, 29, 43, 79043)
        assert pregnancy["diagnosed_date"] == datetime(2018, 7, 28, 16, 29, 43, 79043)
        assert pregnancy["estimated_delivery_date"] == datetime(
            2019, 3, 25, 16, 29, 43, 79043
        )
        assert pregnancy["diagnosed_date_only"] == "2018-07-28"
        assert pregnancy["estimated_delivery_date_only"] == "2019-03-25"

    def test_generate_diabetes_diagnosis(self) -> None:
        conception_date = datetime(2018, 7, 8, 16, 29, 43, 79043)
        clinician_uuid = "dr-jack-newberry-64233"
        medication = {
            "name": "Humalog Mix50",
            "sct_code": "9512801000001102",
            "unit": "units",
            "uuid": "ed870a96-23df-4177-bb0c-575db80caf6f",
        }
        is_pregnant = False

        diagnosis = patient_data.generate_diabetes_diagnosis(
            conception_date,
            clinician_uuid,
            [medication],
            is_pregnant,
            diagnosis_tool_other="Predictive algorithm",
        )

        assert isinstance(diagnosis, Dict)
        assert (
            diagnosis["management_plan"]["doses"][0]["medication_id"]
            == medication["sct_code"]
        )
        assert diagnosis["created_by"] == clinician_uuid
        assert diagnosis["diagnosis_tool"] in patient_data.DIAGNOSIS_TOOL_OPTIONS
        assert diagnosis["sct_code"] in patient_data.DIABETES_TYPES_NOT_PREGNANT

        if diagnosis["diagnosis_tool_other"]:
            assert "D0000018" in diagnosis["diagnosis_tool"]


@pytest.fixture
def sample_medications() -> List[Dict[str, str]]:
    return [
        {
            "name": "Humalog Mix25",
            "sct_code": "9489901000001108",
            "unit": "units",
            "uuid": "5350a08a-070f-48e4-b156-3d6f7ab48efa",
        },
        {
            "name": "Humalog Mix50",
            "sct_code": "9512801000001102",
            "unit": "units",
            "uuid": "ed870a96-23df-4177-bb0c-575db80caf6f",
        },
        {
            "name": "Humulin M3",
            "sct_code": "9530701000001100",
            "unit": "units",
            "uuid": "0a8bb2af-e314-4180-8ac4-fa6a9d7e512b",
        },
        {
            "name": "Novomix 30",
            "sct_code": "9483001000001106",
            "unit": "units",
            "uuid": "f3cf91ed-a04e-48d2-9c8e-02b3492ef23c",
        },
        {
            "name": "Humulin I",
            "sct_code": "9450101000001108",
            "unit": "units",
            "uuid": "76c88ab6-f38a-4a40-9078-1da50d0b5403",
        },
        {
            "name": "Insulatard",
            "sct_code": "9484401000001103",
            "unit": "units",
            "uuid": "437b20da-03b5-496e-91fa-727d1a47531a",
        },
        {
            "name": "Lantus",
            "sct_code": "12759201000001105",
            "unit": "units",
            "uuid": "23b9d0a3-2982-4479-9b42-29d703058579",
        },
        {
            "name": "Levemir",
            "sct_code": "9520901000001101",
            "unit": "units",
            "uuid": "aa5d2790-c8d9-4858-a2a2-ffda64c831d6",
        },
        {
            "name": "Actrapid",
            "sct_code": "9196601000001105",
            "unit": "units",
            "uuid": "c28945e5-198e-4ac5-b6ef-813458d1ab9b",
        },
        {
            "name": "Humulin S",
            "sct_code": "9530801000001109",
            "unit": "units",
            "uuid": "73bb73d9-e892-4fe7-9cd5-d6730899cf6f",
        },
        {
            "name": "Humalog",
            "sct_code": "9538601000001108",
            "unit": "units",
            "uuid": "1fdf2331-70f8-483b-867a-9e764e9e91ff",
        },
        {
            "name": "NovoRapid",
            "sct_code": "9518101000001108",
            "unit": "units",
            "uuid": "69d77158-4f36-4a1e-90e5-f250ea33d4b9",
        },
        {
            "name": "Metformin",
            "sct_code": "109081006",
            "unit": "mg",
            "uuid": "0ee36cf8-945b-4b44-848c-2c73e614bb56",
        },
        {
            "name": "Fiasp",
            "sct_code": "13017301000001108",
            "unit": "units",
            "uuid": "01a31b69-bff8-4124-bbcc-14587c6c3a2b",
        },
        {
            "name": "Tresiba",
            "sct_code": "11706801000001105",
            "unit": "units",
            "uuid": "e2521f7a-b6ab-4c6d-8f0c-916e405bcb7b",
        },
    ]
