import httpx
from she_logging import logger


def catch_and_log_deprecated_route(response: httpx.Response) -> None:
    if response.headers.get("deprecation", False):
        logger.warning(
            "Request to a deprecated route detected: %s %s",
            response.request.method,
            response.request.url,
        )
