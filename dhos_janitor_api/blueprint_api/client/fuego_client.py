from typing import Dict

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.client.common import make_request


def create_fhir_patient(
    clients: ClientRepository, fhir_patient: Dict, system_jwt: str
) -> Dict:
    response = make_request(
        client=clients.dhos_fuego_api,
        method="post",
        url="/dhos/v1/patient_create",
        json=fhir_patient,
        headers={"Authorization": f"Bearer {system_jwt}"},
    )
    return response.json()
