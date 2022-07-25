from typing import Any, Dict

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.client.common import make_request


def create_message(
    clients: ClientRepository, message: Dict, jwt: str, headers: Dict[str, Any]
) -> Dict:
    response = make_request(
        client=clients.dhos_messages_api,
        method="post",
        url="/dhos/v1/message",
        json=message,
        headers={**headers, "Authorization": f"Bearer {jwt}"},
    )
    return response.json()
