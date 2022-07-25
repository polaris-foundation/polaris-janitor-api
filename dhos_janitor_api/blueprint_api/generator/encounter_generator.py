import random
from datetime import date, timedelta
from typing import Dict, Optional

from flask_batteries_included.helpers.timestamp import parse_iso8601_to_date
from she_logging import logger

from dhos_janitor_api.blueprint_api.client import ClientRepository, locations_client


class EncountersGenerator:
    available_locations: Dict[str, Dict]
    ward_sct_code: str
    bay_sct_code: str
    bed_sct_code: str

    def __init__(
        self,
        clients: ClientRepository,
        system_jwt: str,
        ward_sct_code: str,
        bay_sct_code: str,
        bed_sct_code: str,
    ) -> None:
        self.clients = clients
        self.system_jwt = system_jwt
        self.ward_sct_code = ward_sct_code
        self.bay_sct_code = bay_sct_code
        self.bed_sct_code = bed_sct_code
        self.available_locations = self._get_available_locations()

    @staticmethod
    def _random_date(patient: Dict, base_date: Optional[str] = None) -> str:
        if base_date is None:
            base_date = patient["dh_products"][0]["opened_date"]

        base_date_dt = parse_iso8601_to_date(base_date)

        if base_date_dt is None:
            raise ValueError("Couldn't convert base date")

        random_encounter_working = random.randint(5, 10)
        encounter_date = base_date_dt + timedelta(days=random_encounter_working)
        now = date.today()
        final_date = encounter_date if encounter_date < now else now
        return str(final_date)

    def _get_available_locations(self) -> Dict[str, Dict]:
        wards: Dict[str, Dict] = locations_client.get_all_locations(
            clients=self.clients,
            product_name="SEND",
            location_types=[self.ward_sct_code],
            system_jwt=self.system_jwt,
        )
        bays: Dict[str, Dict] = locations_client.get_all_locations(
            clients=self.clients,
            product_name="SEND",
            location_types=[self.bay_sct_code],
            system_jwt=self.system_jwt,
        )
        beds: Dict[str, Dict] = locations_client.get_all_locations(
            clients=self.clients,
            product_name="SEND",
            location_types=[self.bed_sct_code],
            system_jwt=self.system_jwt,
        )

        for bed in beds.values():
            wards.pop(bed["parent"]["uuid"], None)
            bays.pop(bed["parent"]["uuid"], None)

        for bay in bays.values():
            wards.pop(bay["parent"]["uuid"], None)

        return {**wards, **bays, **beds}

    def _gen_random_location(self) -> Dict:
        loc = random.choice(list(self.available_locations.values()))
        if loc["location_type"] == self.bed_sct_code:
            del self.available_locations[loc["uuid"]]
        return loc

    def generate_data_for_patient(
        self, patient: Dict, discharged: bool = False
    ) -> Dict:
        logger.debug(
            "Generating encounter for the patient %s",
            patient["uuid"],
            extra={"discharged": discharged},
        )

        base_date = self._random_date(patient)

        encounter_data = {
            "epr_encounter_id": f"2018L{random.randrange(1, 10**8):08}",
            "encounter_type": "INPATIENT",
            "admitted_at": f"{base_date}T00:00:00.000Z",
            "location_uuid": self._gen_random_location()["uuid"],
            "patient_record_uuid": patient["record"]["uuid"],
            "patient_uuid": patient["uuid"],
            "dh_product_uuid": patient["dh_products"][0]["uuid"],
            "spo2_scale": 1,
            "score_system": "news2",
        }

        if discharged:
            encounter_data[
                "discharged_at"
            ] = f"{self._random_date(patient, base_date=base_date)}T00:00:00.000Z"

        return encounter_data
