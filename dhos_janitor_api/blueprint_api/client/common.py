from typing import Dict, Optional

import httpx
from flask_batteries_included.helpers.error_handler import ServiceUnavailableException
from she_logging import logger


def _log_if_deprecated(response: httpx.Response) -> None:
    if response.headers.get("deprecation", False):
        logger.warning(
            "Request to a deprecated route detected: %s %s",
            response.request.method,
            response.request.url,
        )


def make_request(
    *,
    client: httpx.Client,
    method: str,
    url: str,
    json: Optional[Dict] = None,
    params: Optional[Dict] = None,
    headers: Optional[Dict] = None,
) -> httpx.Response:
    try:
        response = client.request(
            method, url, json=json, params=params, headers=headers, timeout=60
        )
        _log_if_deprecated(response)
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise ServiceUnavailableException(e)
    return response
