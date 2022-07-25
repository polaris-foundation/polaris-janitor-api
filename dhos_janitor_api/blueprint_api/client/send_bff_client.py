from typing import Dict

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.client.common import make_request


def create_observation(
    clients: ClientRepository,
    obs_set: Dict,
    suppress_obs_publish: bool,
    clinician_jwt: str,
) -> Dict:
    response = make_request(
        client=clients.send_bff,
        method="post",
        url="/send/v1/observation_set",
        json=obs_set,
        params={"suppress_obs_publish": suppress_obs_publish},
        headers={"Authorization": f"Bearer {clinician_jwt}"},
    )
    return response.json()


def search_encounters(
    clients: ClientRepository, location_uuid: str, system_jwt: str
) -> Dict:
    response = make_request(
        client=clients.send_bff,
        method="get",
        url="/send/v1/encounter/search",
        params={"location": location_uuid},
        headers={"Authorization": f"Bearer {system_jwt}"},
    )
    return response.json()
