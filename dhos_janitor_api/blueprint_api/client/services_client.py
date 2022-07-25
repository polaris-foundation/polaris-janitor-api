from typing import Dict, List

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.client.common import make_request


def search_patients(
    clients: ClientRepository,
    system_jwt: str,
    product_name: str,
    active: bool = True,
) -> List[Dict]:
    response = make_request(
        client=clients.dhos_services_api,
        method="get",
        url="/dhos/v1/patient/search",
        headers={"Authorization": f"Bearer {system_jwt}"},
        params={"product_name": product_name, "active": active},
    )
    return response.json()


def get_patients_at_location(
    clients: ClientRepository,
    location_uuid: str,
    product_name: str,
    system_jwt: str,
) -> List[Dict]:
    response = make_request(
        client=clients.dhos_services_api,
        method="get",
        url=f"/dhos/v2/location/{location_uuid}/patient",
        headers={"Authorization": f"Bearer {system_jwt}"},
        params={"product_name": product_name, "active": True},
    )
    return response.json()


def create_patient(
    clients: ClientRepository,
    patient_details: Dict,
    product_name: str,
    clinician_jwt: str,
) -> Dict:
    response = make_request(
        client=clients.dhos_services_api,
        method="post",
        url="/dhos/v1/patient",
        params={"product_name": product_name},
        json=patient_details,
        headers={"Authorization": f"Bearer {clinician_jwt}"},
    )
    return response.json()


def update_patient(
    clients: ClientRepository,
    patient_id: str,
    patient_details: Dict,
    jwt: str,
) -> None:
    make_request(
        client=clients.dhos_services_api,
        method="patch",
        url=f"/dhos/v1/patient/{patient_id}",
        json=patient_details,
        headers={"Authorization": f"Bearer {jwt}"},
    )
