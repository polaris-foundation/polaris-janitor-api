from datetime import datetime, timezone
from typing import Dict, List

from flask_batteries_included.helpers.timestamp import parse_datetime_to_iso8601

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.client.common import make_request


def get_encounters_for_patient(
    clients: ClientRepository, patient_id: str, system_jwt: str
) -> List[Dict]:
    response = make_request(
        client=clients.dhos_encounters_api,
        method="get",
        url="/dhos/v2/encounter",
        params={"patient_id": patient_id},
        headers={"Authorization": f"Bearer {system_jwt}"},
    )
    return response.json()


def create_encounter(
    clients: ClientRepository, encounter: Dict, clinician_jwt: str
) -> Dict:
    response = make_request(
        client=clients.dhos_encounters_api,
        method="post",
        url="/dhos/v2/encounter",
        json=encounter,
        headers={"Authorization": f"Bearer {clinician_jwt}"},
    )
    return response.json()


def update_spo2_scale(
    clients: ClientRepository, encounter_id: str, spo2_scale: int, clinician_jwt: str
) -> Dict:
    response = make_request(
        client=clients.dhos_encounters_api,
        method="patch",
        url=f"/dhos/v1/encounter/{encounter_id}",
        json={"spo2_scale": spo2_scale},
        headers={"Authorization": f"Bearer {clinician_jwt}"},
    )
    encounter_details = response.json()
    return encounter_details["score_system_history"][0]


def update_spo2_history(
    clients: ClientRepository,
    score_system_history_id: str,
    spo2_scale_time: datetime,
    system_jwt: str,
) -> datetime:
    spo2_updated_time = spo2_scale_time.replace(tzinfo=timezone.utc)
    spo2_time_data = {"changed_time": parse_datetime_to_iso8601(spo2_updated_time)}
    make_request(
        client=clients.dhos_encounters_api,
        method="patch",
        url=f"/dhos/v1/score_system_history/{score_system_history_id}",
        json=spo2_time_data,
        headers={"Authorization": f"Bearer {system_jwt}"},
    )
    return spo2_scale_time
