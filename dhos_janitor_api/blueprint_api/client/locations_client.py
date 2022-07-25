from typing import Any, Dict, List, Optional, Union

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.client.common import make_request


def get_all_locations(
    clients: ClientRepository,
    product_name: Union[str, List[str]],
    system_jwt: str,
    location_types: Optional[List[str]] = None,
    compact: bool = True,
) -> Dict[str, Dict]:
    params: Dict[str, Any] = {"product_name": product_name, "compact": compact}
    if location_types:
        params["location_types"] = "|".join(location_types)
    response = make_request(
        client=clients.dhos_locations_api,
        method="get",
        url="/dhos/v1/location/search",
        params=params,
        headers={"Authorization": f"Bearer {system_jwt}"},
    )
    return response.json()


def create_location(clients: ClientRepository, location: Dict, system_jwt: str) -> Dict:
    response = make_request(
        client=clients.dhos_locations_api,
        method="post",
        url="/dhos/v1/location",
        json=location,
        headers={"Authorization": f"Bearer {system_jwt}"},
    )
    return response.json()
