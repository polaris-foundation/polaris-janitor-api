import base64
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from auth0_api_client import jwt as auth0_jwt
from cachetools import TTLCache, cached
from jose import jwt as jose_jwt
from she_logging import logger

from dhos_janitor_api.blueprint_api.client import (
    ClientRepository,
    activation_auth_client,
)
from dhos_janitor_api.config import Configuration

DATA_DIR_PATH: Path = Path(__file__).parent.parent.parent / "data"
DHOS_SERVICES_DATA_PATH: Path = DATA_DIR_PATH / "dhos_services_data.json"
ROLES_DATA_PATH: Path = DATA_DIR_PATH / "roles_definition.json"


@cached(
    TTLCache(
        maxsize=16,
        ttl=Configuration.SYSTEM_JWT_LIFETIME_SECONDS
        * Configuration.JWT_TTL_COEFFICIENT,
    )
)
def get_system_jwt(system_id: str = "dhos-robot") -> str:
    logger.info("Creating system JWT for system ID '%s'", system_id)
    jwt_token: str = jose_jwt.encode(
        {
            "metadata": {"can_edit_ews": True, "system_id": system_id},
            "iss": Configuration.HS_ISSUER,
            "aud": Configuration.PROXY_URL,
            "scope": " ".join(_get_permissions_for_group("System")),
            "exp": datetime.utcnow()
            + timedelta(seconds=Configuration.SYSTEM_JWT_LIFETIME_SECONDS),
        },
        key=Configuration.HS_KEY,
        algorithm="HS512",
    )

    logger.info("Created system JWT for system ID '%s'", system_id)
    return jwt_token


@cached(
    TTLCache(
        maxsize=128,
        ttl=Configuration.CLINICIAN_JWT_LIFETIME_SECONDS
        * Configuration.JWT_TTL_COEFFICIENT,
    )
)
def get_clinician_jwt(
    username: str,
    password: Optional[str] = None,
    clinician_uuid: Optional[str] = None,
    use_auth0: bool = False,
) -> str:
    logger.debug(
        "No unexpired cached clinician JWT for %s, getting a new one", username
    )

    if not username:
        raise ValueError(f"username is missing")

    if not use_auth0:
        clinician_data: Dict = _get_clinician_data(username, clinician_uuid)
        clinician_groups: List[str] = clinician_data["groups"]
        clinician_permissions: Set[str] = set()
        for group in clinician_groups:
            clinician_permissions.update(_get_permissions_for_group(group))

        clinician_metadata: Dict = {
            "clinician_id": clinician_data.get("uuid", clinician_uuid),
            "job_title": clinician_data.get("job_title", None),
            "products": clinician_data.get("products", []),
            "can_edit_ews": clinician_data.get("can_edit_ews", False),
        }

        clinician_jwt = jose_jwt.encode(
            {
                "metadata": clinician_metadata,
                "iss": Configuration.HS_ISSUER,
                "aud": Configuration.PROXY_URL,
                "scope": " ".join(clinician_permissions),
                "exp": datetime.utcnow()
                + timedelta(seconds=Configuration.CLINICIAN_JWT_LIFETIME_SECONDS),
            },
            key=Configuration.HS_KEY,
            algorithm="HS512",
        )

        logger.info(
            "Created JWT for clinician with %s: %s",
            "email" if username else "uuid",
            username if username else clinician_uuid,
        )
        return clinician_jwt

    logger.debug("Getting clinician JWT from auth0 for %s", username)

    if not password:
        raise ValueError(f"password is missing")

    user_jwt: str = auth0_jwt.get_auth0_jwt_for_user(username, password)
    return user_jwt


@cached(
    TTLCache(
        maxsize=128,
        ttl=Configuration.PATIENT_JWT_LIFETIME_SECONDS
        * Configuration.JWT_TTL_COEFFICIENT,
    )
)
def get_patient_jwt(clients: ClientRepository, patient_id: str) -> str:
    logger.debug(
        "No unexpired cached patient JWT for %s, getting a new one", patient_id
    )

    if patient_id in map(str, range(1, 10)):
        activation_code = patient_id
        otp = patient_id * 4
    else:
        logger.debug("Creating activation for patient with UUID %s", patient_id)
        activation: Dict = activation_auth_client.create_activation_for_patient(
            clients, patient_id, get_system_jwt()
        )
        logger.debug("Created activation for patient with UUID %s", patient_id)
        activation_code = activation["activation_code"]
        otp = activation["otp"]

    # GET AUTHORISATION CODE
    authorisation_code = activation_auth_client.create_activation(
        clients, activation_code, otp
    )["authorisation_code"]

    # GET JWT
    logger.debug("Getting jwt for patient with UUID %s", patient_id)
    return activation_auth_client.get_patient_jwt(
        clients, patient_id, authorisation_code
    )["jwt"]


def get_auth_from_b64_basic_auth(auth_header: Optional[str]) -> Tuple:
    if auth_header is None or not auth_header.startswith("Basic "):
        return None, None

    b64_encoded_auth = auth_header[6:].encode("ascii")

    decoded_u_p = base64.b64decode(b64_encoded_auth).decode("ascii").split(":", 1)

    username = decoded_u_p[0]
    password = decoded_u_p[1]

    return username, password


def _get_permissions_for_group(group: str) -> List[str]:
    roles_data: Dict = json.loads(ROLES_DATA_PATH.read_text())
    role: Optional[Dict] = next(
        (r for r in roles_data["roles"] if r["name"] == group), None
    )

    if role is None:
        raise ValueError("No scopes found for role %s", group)

    return role["permissions"]


def _get_clinician_data(
    username: Optional[str] = None, clinician_uuid: Optional[str] = None
) -> Dict:
    if username is None and clinician_uuid is None:
        raise ValueError("Either username of clinician uuid should be provided")

    dhos_services_data: Dict = json.loads(DHOS_SERVICES_DATA_PATH.read_text())
    clinician_data: List[Dict] = dhos_services_data["clinician"]
    clinicians: List[Dict] = [
        c
        for c in clinician_data
        if (username and c["email_address"] == username)
        or (clinician_uuid and c["uuid"] == clinician_uuid)
    ]

    if not clinicians:
        raise ValueError(
            f"No clinicians found with username {username} and/or uuid {clinician_uuid}."
        )

    elif len(clinicians) > 1:
        logger.warning(
            "More than 1 clinician found with username %s and/or uuid %s",
            username,
            clinician_uuid,
        )

    return clinicians[0]


def has_expired(jwt: str) -> bool:
    try:
        jose_jwt.decode(
            jwt,
            "dummykey",
            options={
                "verify_signature": False,
                "verify_aud": False,
                "verify_iat": False,
                "verify_exp": True,
                "verify_nbf": False,
                "verify_iss": False,
                "verify_sub": False,
                "verify_jti": False,
                "verify_at_hash": False,
                "leeway": 0,
            },
        )
    except jose_jwt.ExpiredSignatureError:
        return True
    else:
        return False
