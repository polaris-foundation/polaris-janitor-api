from typing import Dict

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.client.common import make_request


def create_reading(
    clients: ClientRepository, patient_id: str, patient_jwt: str, reading_details: Dict
) -> Dict:
    response = make_request(
        client=clients.gdm_bff,
        method="post",
        url=f"/gdm/v1/patient/{patient_id}/reading",
        json=reading_details,
        headers={"Authorization": f"Bearer {patient_jwt}"},
    )
    return response.json()
