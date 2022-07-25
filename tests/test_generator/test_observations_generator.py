from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from flask_batteries_included.helpers.timestamp import parse_datetime_to_iso8601

from dhos_janitor_api.blueprint_api.generator.observations_generator import (
    OBSERVATION_TYPES,
    ObservationsGenerator,
    Trajectory,
)

OBS_TYPES = [
    "temperature",
    "systolic_blood_pressure",
    "diastolic_blood_pressure",
    "heart_rate",
    "respiratory_rate",
    "spo2",
    "consciousness_acvpu",
    "nurse_concern",
    "o2_therapy_status",
]


@pytest.mark.usefixtures("app")
class TestObservationsGenerator:
    def test_generate(self) -> None:
        encounter_uuid: str = "encounter_uuid"
        time_now: datetime = datetime.now().replace(tzinfo=timezone.utc)

        for trajectory in [
            Trajectory.FINE,
            Trajectory.A_BIT_ILL,
            Trajectory.MEDIUM_ILL,
            Trajectory.VERY_ILL,
        ]:
            obs_set: Dict = ObservationsGenerator.generate(
                encounter_uuid, 1, time_now, trajectory
            )

            assert obs_set["record_time"] == parse_datetime_to_iso8601(time_now)
            assert obs_set["encounter_id"] == encounter_uuid
            assert obs_set["score_system"] == "news2"
            assert obs_set["spo2_scale"] in [1, 2]

            for obs in obs_set["observations"]:
                assert obs["observation_type"] in OBS_TYPES
                assert (
                    obs.get("observation_string") is None
                    and obs.get("observation_value") is None
                    and obs.get("patient_refused", False) is False
                ) is False

    def test_resp_rate_unit(self, mocker: Any) -> None:
        """
        This test was added after changing the observation unit for "respiratory_rate" obs
        It just ensures that the change worked. We've patched a method to ensure resp rate is
        generated.
        """
        mocker.patch.object(
            ObservationsGenerator, "_choose_obs_subset", return_value=OBSERVATION_TYPES
        )
        encounter_uuid: str = "encounter_uuid"
        time_now = datetime.now().replace(tzinfo=timezone.utc)
        obs_set: Dict = ObservationsGenerator.generate(
            encounter_uuid, 1, time_now, Trajectory.MEDIUM_ILL
        )

        resp_rate_ob = next(
            (
                o
                for o in obs_set["observations"]
                if o["observation_type"] == "respiratory_rate"
            ),
            None,
        )
        assert resp_rate_ob is not None
        assert resp_rate_ob["observation_unit"] == "per min"
