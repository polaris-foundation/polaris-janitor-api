from datetime import datetime

import pytest
from pytest_mock import MockFixture

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.generator import encounter_generator


@pytest.mark.usefixtures("app")
class TestEncounterGenerator:
    @pytest.fixture
    def generator(
        self, clients: ClientRepository, system_jwt: str, mocker: MockFixture
    ) -> encounter_generator.EncountersGenerator:
        ward_sct_code = "111"
        bay_sct_code = "222"
        bed_sct_code = "333"

        mocker.patch.object(
            encounter_generator.locations_client, "get_all_locations", return_value={}
        )

        return encounter_generator.EncountersGenerator(
            clients, system_jwt, ward_sct_code, bay_sct_code, bed_sct_code
        )

    @pytest.mark.parametrize("valid", (True, False))
    @pytest.mark.parametrize("base_date", (None, "2021-10-14"))
    def test_random_date(
        self,
        generator: encounter_generator.EncountersGenerator,
        valid: bool,
        base_date: str,
    ) -> None:
        patient = {"dh_products": [{"opened_date": datetime.now().date().isoformat()}]}
        if not valid:
            with pytest.raises(ValueError):
                generator._random_date(patient, "asdasd")
            return

        result = generator._random_date(patient, base_date)
        assert isinstance(result, str)

    def test_get_available_locations(
        self, generator: encounter_generator.EncountersGenerator, mocker: MockFixture
    ) -> None:
        mock_get_all_locations = mocker.patch.object(
            encounter_generator.locations_client,
            "get_all_locations",
            return_value={
                "123": {"parent": {"uuid": "321"}},
            },
        )
        result = generator._get_available_locations()
        assert mock_get_all_locations.call_count == 3
        assert "123" in result
        assert len(result) == 1
