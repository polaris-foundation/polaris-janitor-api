import random
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import draymed
from flask_batteries_included.helpers.timestamp import (
    parse_datetime_to_iso8601,
    parse_iso8601_to_datetime,
)
from she_logging import logger

# snomed codes for meals and the respective prandial tags for their equivalent "before x type of meal" reading
SNOMED_TO_PRANDIAL_TAG = {"1751000175104": 1, "1761000175102": 3, "1771000175105": 5}

# Any generated reading below this value will be re-generated.
MIN_READING_VALUE = 1

# Glucose profiles. the array for each entry represents several values used to generated each reading:
#   [0] - Mean value Normal Standard Distribution;
#   [1] - Sigma value for the Normal Standard Distribution;
#   [2] - Added Value if its a "post" prandial tag.
#   [3] - the percentage value of a missing reading / missing medication.
#   [4] - Chance that the patient takes another reading for a single prandial tag
PROFILES = {
    "HIGH": [5.0, 3.0, 3.0, 0.7, 0.2],
    "AVERAGE": [5.0, 2.0, 2.0, 0.3, 0.1],
    "LOW": [5.0, 1.0, 1.0, 0.1, 0.1],
    "RANDOM": [5.0, 2.0, 1.0, 0.5, 0.4],
}

# the index of PRANDIAL_REF_TIME represents the related prandial_tag;
# for each sub array entry, the index 0 represents the time reference, the index 1 represents the max deviation
# (in hours) from the time reference.
PRANDIAL_REF_TIME: List[List] = [
    # this is here because prandial tags start at 1, this assures that whatever prandial tag is selected,
    # it serves as index for this array
    [],
    ["07:00", 1],
    ["09:00", 1],
    ["12:30", 1],
    ["14:30", 1],
    ["19:30", 1],
    ["21:30", 1],
    ["12:00", 12],
]

COMMENT_LIST = [
    "I ate earlier than usual today",
    "Had some cake, sorry!",
    "I don't feel very well at the moment",
    "Not sure if I should take more insulin",
    "I didn't eat very much",
    "I feel much better today!",
    "Eaten nothing yet today",
    "Is this better?",
]

PRANDIAL_TAG_UUID_MAP = {
    0: "PRANDIAL-TAG-NONE",
    1: "PRANDIAL-TAG-BEFORE-BREAKFAST",
    2: "PRANDIAL-TAG-AFTER-BREAKFAST",
    3: "PRANDIAL-TAG-BEFORE-LUNCH",
    4: "PRANDIAL-TAG-AFTER-LUNCH",
    5: "PRANDIAL-TAG-BEFORE-DINNER",
    6: "PRANDIAL-TAG-AFTER-DINNER",
    7: "PRANDIAL-TAG-OTHER",
}

diabetes_sct_codes = list(draymed.codes.list_category("diabetes_type").keys())


class ReadingsGenerator:
    patient: Optional[Dict] = None
    glucose_profile: str

    def __init__(
        self, patient: Optional[Dict], glucose_profile: Optional[str] = None
    ) -> None:
        self.patient = patient

        if glucose_profile is None or glucose_profile not in [*PROFILES]:
            self.glucose_profile = random.choice([*PROFILES])
            logger.debug(
                "No Glucose Profile, selecting one at random: %s",
                self.glucose_profile,
            )
        else:
            logger.debug("Using Glucose Profile: %s", self.glucose_profile)
            self.glucose_profile = glucose_profile

    def generate_data(self) -> List[Dict]:
        if self.patient is None:
            raise ValueError("Patient object missing")

        if self.glucose_profile is None:
            raise ValueError("No glucose profile generated")

        selected_diagnosis = self._get_diagnosis()

        # calculate differential from number of readings per day vs how many medication plans exist
        requested_doses = self._get_doses(selected_diagnosis)
        requested_readings = self._get_readings(selected_diagnosis)

        # EDGE CASE: what if neither of the previous vars exist? no readings at all?
        max_readings_day, working_days = self._get_schedule(
            requested_readings, requested_doses
        )

        logger.debug("Generating BG reading data for %d days", working_days)

        readings_list: List[Dict] = []
        missed_readings: int = 0

        for differential in range(1, working_days):
            now = datetime.utcnow()
            current_day_start: datetime = now - timedelta(
                days=differential,
                hours=now.hour,
                minutes=now.minute,
                seconds=now.second,
                microseconds=now.microsecond,
            )

            # controller lists to avoid overlapping information while creating the different readings for each day
            working_meal_types = [*SNOMED_TO_PRANDIAL_TAG]
            working_prandial_tags = [1, 2, 3, 4, 5, 6, 7]
            single_day_readings: List[Dict] = []

            daily_reading_control = max_readings_day

            logger.debug(
                "Generating BG readings for %d days ago (resulting date %s)",
                differential,
                current_day_start,
            )
            while len(single_day_readings) < daily_reading_control:
                meds: List[Dict] = []
                # we are using the management plan as base for the readings created in such a way that, unless the
                # reading miss, we created 1 reading per day for each of the entries on the management plan and then,
                # if the readings plan requires more readings we add more at random
                if len(working_meal_types) > 0:
                    current_meal = working_meal_types.pop()
                    meds = list(
                        filter(
                            lambda dose: dose["routine_sct_code"] == current_meal,
                            requested_doses,
                        )
                    )
                    selected_prandial_tag = SNOMED_TO_PRANDIAL_TAG[current_meal]

                    # if there is no items on the meds list it means there is no medication for the selected meal type
                    # by skipping the loop here the only thing that happens is that the list of working meal types
                    # shrinks by one and it will eventually be empty. Once empty the code will skip this first half
                    # and jump directly to the else, generating readings without medications attached
                    if len(meds) == 0:
                        continue
                else:
                    selected_prandial_tag = random.choice(working_prandial_tags)
                working_prandial_tags.remove(selected_prandial_tag)

                # Depending on the user profile there is a higher or lower chance to miss the reading
                if self.did_user_miss(self.glucose_profile):
                    missed_readings += 1
                    daily_reading_control -= 1
                    continue

                single_day_readings.append(
                    self.create_reading(
                        date_start=current_day_start,
                        prandial_tag=selected_prandial_tag,
                        medication_list=meds,
                    )
                )

                while self.did_user_take_extra(self.glucose_profile):
                    single_day_readings.append(
                        self.create_reading(
                            date_start=current_day_start,
                            prandial_tag=selected_prandial_tag,
                        )
                    )

            readings_list = readings_list + single_day_readings

        logger.debug(
            "BG reading generation complete",
            extra={
                "generated_readings": len(readings_list),
                "missed_readings": missed_readings,
                "max_readings_day": max_readings_day,
                "total_days": working_days - 1,
                "profile": self.glucose_profile,
            },
        )

        readings_list.sort(key=lambda item: item["created"])

        return readings_list

    def create_reading(
        self,
        date_start: Optional[datetime] = None,
        prandial_tag: Optional[int] = None,
        medication_list: Optional[List[Dict]] = None,
    ) -> Dict:

        if prandial_tag is None:
            prandial_tag = random.randint(1, 7)

        if date_start is None:
            # Default to start of today.
            now = datetime.utcnow()
            date_start = now - timedelta(
                hours=now.hour,
                minutes=now.minute,
                seconds=now.second,
                microseconds=now.microsecond,
            )

        if medication_list is None:
            medication_list = []

        doses: List[Dict] = []

        if self.glucose_profile is None:
            raise ValueError("No glucose profile for readings generation")

        reading_value = self.generate_reading_value(
            profile_values=PROFILES[self.glucose_profile], prandial_tag=prandial_tag
        )
        final_datetime = parse_datetime_to_iso8601(
            self.generate_datetime_by_prandial(date_start, prandial_tag)
        )

        for medication in medication_list:
            # Depending on the user profile there is a higher or lower chance to miss the medication
            if self.did_user_miss(self.glucose_profile):
                continue

            med_dict = {
                "amount": round(random.uniform(0.0, 99.0), 1),
                "medication_id": medication["medication_id"],
            }
            doses.insert(0, med_dict)

        return {
            "measured_timestamp": final_datetime,
            "blood_glucose_value": reading_value,
            "prandial_tag": {
                "value": prandial_tag,
                "uuid": PRANDIAL_TAG_UUID_MAP[prandial_tag],
            },
            "units": "mmol/L",
            "comment": self.generate_comment(),
            "created": final_datetime,
            "doses": doses,
        }

    # calculate the number of days the patient will have with readings based on a random from today
    # to the day of the patient creation. Max 40 days.
    @staticmethod
    def calculate_working_days(closest_date: datetime, furthest_date: datetime) -> int:
        # adding a TZ to 'closest_date' so it can be used against another tz aware date after
        closest_date = closest_date.replace(tzinfo=timezone(timedelta(seconds=0)))
        delta = closest_date - furthest_date
        return random.randint(0, min(delta.days, 40))

    @staticmethod
    def generate_comment() -> str:
        return random.choice(COMMENT_LIST)

    @staticmethod
    def generate_reading_value(profile_values: List[float], prandial_tag: int) -> float:
        # normal distribution based on the given profile plus the
        # increased impact if the prandial tag is a post meal one
        result: float = -1
        while result < MIN_READING_VALUE:
            result = round(
                random.normalvariate(mu=profile_values[0], sigma=profile_values[1])
                + ((0 if prandial_tag % 2 == 0 else 1) * profile_values[2]),
                1,
            )

        return result

    @staticmethod
    def generate_datetime_by_prandial(date: datetime, prandial_tag: int) -> datetime:
        # sigma value, converted to seconds
        sigma = PRANDIAL_REF_TIME[prandial_tag][1] * 60 * 60
        base_time = time.strptime(PRANDIAL_REF_TIME[prandial_tag][0], "%H:%M")

        result = date + timedelta(
            hours=base_time.tm_hour,
            minutes=base_time.tm_min,
            seconds=random.normalvariate(mu=0, sigma=sigma),
        )

        return result.replace(tzinfo=timezone(timedelta(seconds=0)))

    @staticmethod
    def did_user_miss(profile: str) -> bool:
        return random.random() <= PROFILES[profile][3]

    @staticmethod
    def did_user_take_extra(profile: str) -> bool:
        return random.random() <= PROFILES[profile][4]

    def _get_diagnosis(self) -> Dict:
        if self.patient is None:
            raise ValueError("No patient data")
        try:
            selected_diagnosis = list(
                filter(
                    lambda dio: dio["sct_code"] in diabetes_sct_codes,
                    self.patient["record"]["diagnoses"],
                )
            )[0]
        except (KeyError, IndexError):
            logger.exception("Patient's diagnosis has unknown SCT code")
            raise ValueError("Valid Diagnosis missing.")
        return selected_diagnosis

    @staticmethod
    def _get_doses(diagnosis: Dict) -> List[Dict]:
        requested_doses = diagnosis.get("management_plan", {}).get("doses", [])
        logger.debug("Found %d doses in management plan", len(requested_doses))
        return requested_doses

    @staticmethod
    def _get_readings(diagnosis: Dict) -> int:
        requested_readings = diagnosis.get("readings_plan", {}).get(
            "readings_per_day", None
        )
        if requested_readings is not None:
            logger.debug("Expecting %d readings per day", requested_readings)
        else:
            logger.info("Readings plan missing, ignoring")
            requested_readings = 0
        return requested_readings

    def _get_schedule(
        self, requested_readings: int, requested_doses: List[Dict]
    ) -> Tuple[int, int]:
        if self.patient is None:
            raise ValueError("No patient data")
        max_readings_day = (
            requested_readings
            if requested_readings > len(requested_doses)
            else requested_readings
        )

        patient_created_dt = parse_iso8601_to_datetime(self.patient["created"])
        if patient_created_dt is None:
            raise ValueError("Patient has no created date")
        working_days = self.calculate_working_days(
            closest_date=datetime.utcnow(), furthest_date=patient_created_dt
        )
        return max_readings_day, working_days
