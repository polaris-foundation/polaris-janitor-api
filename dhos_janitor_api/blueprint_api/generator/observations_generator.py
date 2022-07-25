import random
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Union

from flask_batteries_included.helpers.timestamp import parse_datetime_to_iso8601


class Trajectory(Enum):
    VERY_ILL = 0
    MEDIUM_ILL = 1
    A_BIT_ILL = 2
    FINE = 3


OBSERVATION_TYPES = [
    "temperature",
    "systolic_and_diastolic_blood_pressure",
    "heart_rate",
    "respiratory_rate",
    "spo2",
    "consciousness_acvpu",
    "nurse_concern",
    "mask_type",
]


OBSERVATIONS_UNABLE_TO_REFUSE = [
    "o2_therapy_status",
    "consciousness_acvpu",
    "nurse_concern",
]

BLOOD_PRESSURES = ["systolic_blood_pressure", "diastolic_blood_pressure"]


class ObservationsGenerator:
    @classmethod
    def generate(
        cls,
        encounter_id: str,
        current_spo2_scale: int,
        record_time: datetime,
        trajectory: Trajectory,
    ) -> Dict:

        obs_types: List[str] = cls._choose_obs_subset()

        observations: List[Dict] = []
        for obs_type in obs_types:

            obs_record_time_dt = record_time + timedelta(minutes=random.randint(0, 3))
            obs_record_time = obs_record_time_dt.replace(
                tzinfo=timezone.utc
            ).isoformat()

            generate_function = getattr(ObservationsGenerator, f"_get_{obs_type}")
            generated_obs = generate_function(trajectory)

            if generated_obs is None:
                continue

            if isinstance(generated_obs, dict):
                generated_obs = [generated_obs]

            for obs in generated_obs:
                obs["measured_time"] = obs_record_time
                if (
                    obs["observation_type"]
                    not in OBSERVATIONS_UNABLE_TO_REFUSE + BLOOD_PRESSURES
                    and random.random() > 0.95
                ):
                    obs["patient_refused"] = True
                    obs.pop("observation_value", None)
                    obs.pop("observation_string", None)
                    obs.pop("observation_metadata", None)

            observations += generated_obs

        return {
            "record_time": parse_datetime_to_iso8601(record_time),
            "encounter_id": encounter_id,
            "score_system": "news2",
            "observations": observations,
            "spo2_scale": current_spo2_scale,
        }

    @staticmethod
    def get_random_trajectory() -> Trajectory:
        rand = random.random()
        if rand > 0.95:
            return Trajectory.VERY_ILL
        if rand > 0.90:
            return Trajectory.MEDIUM_ILL
        if rand > 0.75:
            return Trajectory.A_BIT_ILL
        return Trajectory.FINE

    @staticmethod
    def _choose_obs_subset() -> List[str]:
        rand = random.random()
        if rand > 0.2:
            # 80% of complete set
            n_obs = len(OBSERVATION_TYPES)
        elif rand > 0.05:
            # 15% chance missing one or two
            n_obs = len(OBSERVATION_TYPES) - random.randint(0, 3)
        else:
            # 5% chance missing loads
            n_obs = len(OBSERVATION_TYPES) - random.randint(
                3, (len(OBSERVATION_TYPES) - 1)
            )

        shuffled_types = OBSERVATION_TYPES[:]
        random.shuffle(shuffled_types)
        return shuffled_types[:n_obs]

    @staticmethod
    def _get_spo2_scale(trajectory: Trajectory) -> int:
        if trajectory == Trajectory.VERY_ILL:
            thresh = 0.2
        elif trajectory == Trajectory.MEDIUM_ILL:
            thresh = 0.5
        elif trajectory == Trajectory.A_BIT_ILL:
            thresh = 0.9
        else:
            thresh = 0.95
        return 2 if random.random() > thresh else 1

    @staticmethod
    def _get_temperature(trajectory: Trajectory) -> Dict:
        if trajectory == Trajectory.FINE:
            greater_than = 36.5
            less_than = 37.5
        elif trajectory == Trajectory.A_BIT_ILL:
            greater_than = 36
            less_than = 38.5
        elif trajectory == Trajectory.MEDIUM_ILL:
            greater_than = 35
            less_than = 39
        else:
            greater_than = 34
            less_than = 40
        value = round(random.uniform(greater_than, less_than), 1)
        return {
            "observation_type": "temperature",
            "observation_value": value,
            "observation_unit": "celcius",
        }

    @classmethod
    def _get_systolic_and_diastolic_blood_pressure(
        cls, trajectory: Trajectory
    ) -> List[Dict]:
        if trajectory == Trajectory.FINE:
            greater_than = 110
            less_than = 140
        elif trajectory == Trajectory.A_BIT_ILL:
            greater_than = 100
            less_than = 150
        elif trajectory == Trajectory.MEDIUM_ILL:
            greater_than = 90
            less_than = 200
        else:
            greater_than = 80
            less_than = 240
        systolic_value: int = random.randint(greater_than, less_than)
        diastolic_value: int = systolic_value - random.randint(40, 60)
        position: str = random.choice(["sitting", "standing", "lying"])

        observations = [
            {
                "observation_type": "systolic_blood_pressure",
                "observation_value": systolic_value,
                "observation_unit": "mmHg",
                "observation_metadata": {"patient_position": position},
            },
            {
                "observation_type": "diastolic_blood_pressure",
                "observation_value": diastolic_value,
                "observation_unit": "mmHg",
                "observation_metadata": {"patient_position": position},
            },
        ]
        if random.random() > 0.95:
            for obs in observations:
                obs["patient_refused"] = True
                obs.pop("observation_value", None)
                obs.pop("observation_string", None)
                obs.pop("observation_metadata", None)

        return observations

    @staticmethod
    def _get_heart_rate(trajectory: Trajectory) -> Dict:
        if trajectory == Trajectory.FINE:
            greater_than = 51
            less_than = 90
        elif trajectory == Trajectory.A_BIT_ILL:
            greater_than = 50
            less_than = 110
        elif trajectory == Trajectory.MEDIUM_ILL:
            greater_than = 40
            less_than = 130
        else:
            greater_than = 35
            less_than = 180
        value = random.randint(greater_than, less_than)

        return {
            "observation_type": "heart_rate",
            "observation_value": value,
            "observation_unit": "bpm",
        }

    @staticmethod
    def _get_respiratory_rate(trajectory: Trajectory) -> Dict:
        if trajectory == Trajectory.FINE:
            greater_than = 12
            less_than = 20
        elif trajectory == Trajectory.A_BIT_ILL:
            greater_than = 9
            less_than = 24
        elif trajectory == Trajectory.MEDIUM_ILL:
            greater_than = 7
            less_than = 30
        else:
            greater_than = 5
            less_than = 60
        value = random.randint(greater_than, less_than)
        return {
            "observation_type": "respiratory_rate",
            "observation_value": value,
            "observation_unit": "per min",
        }

    @staticmethod
    def _get_spo2(trajectory: Trajectory) -> Dict:
        if trajectory == Trajectory.FINE:
            greater_than = 96
            less_than = 100
        elif trajectory == Trajectory.A_BIT_ILL:
            greater_than = 94
            less_than = 100
        elif trajectory == Trajectory.MEDIUM_ILL:
            greater_than = 92
            less_than = 100
        else:
            greater_than = 80
            less_than = 100
        value = random.randint(greater_than, less_than)
        return {
            "observation_type": "spo2",
            "observation_value": value,
            "observation_unit": "%",
        }

    @staticmethod
    def _get_consciousness_acvpu(trajectory: Trajectory) -> Dict:
        if trajectory == Trajectory.FINE:
            consciousness = "Alert"
        elif trajectory == Trajectory.A_BIT_ILL:
            consciousness = random.choice(["Alert", "Confusion"])
        elif trajectory == Trajectory.MEDIUM_ILL:
            consciousness = random.choice(["Alert", "Confusion", "Voice"])
        else:
            consciousness = random.choice(
                ["Confusion", "Voice", "Pain", "Unresponsive"]
            )

        return {
            "observation_type": "consciousness_acvpu",
            "observation_string": consciousness,
        }

    @staticmethod
    def _get_nurse_concern(trajectory: Trajectory) -> Union[Dict, None]:
        if trajectory == Trajectory.FINE:
            threshold = 0.95
        elif trajectory == Trajectory.A_BIT_ILL:
            threshold = 0.9
        elif trajectory == Trajectory.MEDIUM_ILL:
            threshold = 0.6
        else:
            threshold = 0.4
        if random.random() < threshold:
            return None

        nurse_concern = [
            "Airway Compromise",
            "Bleeding/Melaena",
            "Pallor or Cyanosis",
            "New Facial/Limb Weakness",
            "Diarrhoea/Vomiting",
            "Abnormal Electrolyte/BG",
            "Unresolved Pain",
            "Self Harm",
            "Infection?",
            "Shock (HR > BP)",
            "Non-specific Concern",
        ]

        return {
            "observation_type": "nurse_concern",
            "observation_string": random.choice(nurse_concern),
        }

    @staticmethod
    def _get_mask_type(trajectory: Trajectory) -> Dict:

        if trajectory == Trajectory.FINE:
            threshold = 0.95
        elif trajectory == Trajectory.A_BIT_ILL:
            threshold = 0.85
        elif trajectory == Trajectory.MEDIUM_ILL:
            threshold = 0.5
        else:
            threshold = 0.2

        if random.random() < threshold:
            return {
                "observation_type": "o2_therapy_status",
                "observation_value": 0,
                "observation_unit": "lpm",
                "observation_metadata": {"mask": "Room Air"},
            }

        masks = [
            "Venturi",
            "Humidified",
            "Nasal Cann.",
            "Simple",
            "Resv Mask",
            "CPAP",
            "NIV",
            "High Flow",
        ]

        mask = random.choice(masks)
        observation_metadata: Dict[str, Any] = {"mask": mask}

        if mask == "High Flow":
            observation_value = random.randint(1, 100)
            observation_unit = "%"
        else:
            observation_value = int(round(random.uniform(0.5, 15), 1))
            observation_unit = "lpm"
        if mask == "Venturi":
            observation_metadata["mask_percent"] = random.choice([24, 28, 35, 40, 60])
        elif mask == "Humidified":
            observation_metadata["mask_percent"] = random.choice(
                [28, 35, 40, 60, 80, 98]
            )

        return {
            "observation_type": "o2_therapy_status",
            "observation_value": observation_value,
            "observation_unit": observation_unit,
            "observation_metadata": observation_metadata,
        }
