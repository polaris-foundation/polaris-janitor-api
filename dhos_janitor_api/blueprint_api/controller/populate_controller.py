import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from flask_batteries_included.helpers import generate_uuid
from she_logging import logger
from she_logging.request_id import current_request_id

from dhos_janitor_api.blueprint_api.client import (
    ClientRepository,
    gdm_bff_client,
    messages_client,
    services_client,
    users_client,
)
from dhos_janitor_api.blueprint_api.controller import auth_controller, reset_controller
from dhos_janitor_api.blueprint_api.generator import (
    message_generator,
    readings_generator,
)
from dhos_janitor_api.blueprint_api.janitor_thread import JanitorThread

MESSAGE_PROBABILITY: float = 0.33
VISIT_PROBABILITY: float = 0.1


def start_populate_gdm_thread(days: int, use_system_jwt: bool) -> str:
    task_uuid: str = generate_uuid()

    thread = JanitorThread(
        task_uuid=task_uuid,
        target=populate_gdm_data,
        request_id=current_request_id(),
        require_context=True,
    )
    thread.start(days=days, use_system_jwt=use_system_jwt)
    return task_uuid


def populate_gdm_data(
    clients: ClientRepository, days: int, use_system_jwt: bool
) -> None:
    system_jwt = auth_controller.get_system_jwt()
    # Note: this function actually adds data for both GDM and DBM patients.
    logger.info("Populating GDM/DBM data for last %d days", days)
    gdm_patients: Dict[str, Dict] = {
        p["uuid"]: p
        for p in services_client.search_patients(
            clients=clients,
            product_name="GDM",
            system_jwt=system_jwt,
        )
    }
    gdm_clinicians: Dict[str, Dict] = {
        c["uuid"]: c
        for c in users_client.get_clinicians(
            clients=clients,
            product_name="GDM",
            system_jwt=system_jwt,
        )
    }

    logger.info("Found %d GDM patients", len(gdm_patients))
    for patient in gdm_patients.values():
        _populate_for_patient(
            clients=clients,
            patient=patient,
            clinician=reset_controller.get_random_clinician(
                list(gdm_clinicians.values()), {"GDM Superclinician"}
            ),
            days=days,
            use_system_jwt=use_system_jwt,
        )

    # Some DBM patients don't have locations, so we can't iterate through locations to get a list of patients.
    # Instead we use the search endpoint, but sadly it doesn't contain the readings plan so we have to also
    # GET the patient by UUID before we can generate readings.
    dbm_patients: List[Dict] = services_client.search_patients(
        clients=clients,
        system_jwt=system_jwt,
        product_name="DBM",
        active=True,
    )
    logger.info("Found %d DBM patients", len(dbm_patients))
    for patient in dbm_patients:
        _populate_for_patient(
            clients=clients,
            patient=patient,
            clinician=reset_controller.get_random_clinician(
                # For now, use GDM Superclinicians because they have more permissions.
                list(gdm_clinicians.values()),
                {"GDM Superclinician"},
            ),
            days=days,
            use_system_jwt=use_system_jwt,
        )

    logger.info("Finished populating GDM/DBM data")


def _populate_for_patient(
    clients: ClientRepository,
    patient: Dict,
    clinician: Dict,
    days: int,
    use_system_jwt: bool,
) -> None:
    logger.info("Populating diabetes data for patient %s", patient["uuid"])
    # Get diagnosis or skip patient.
    diagnosis: Optional[Dict] = next(
        (
            d
            for d in patient["record"]["diagnoses"]
            if d["sct_code"] in readings_generator.diabetes_sct_codes
        ),
        None,
    )
    if diagnosis is None or not diagnosis.get("readings_plan"):
        logger.debug(
            "Skipping patient %s - no diabetes diagnosis with readings plan",
            patient["uuid"],
        )
        return

    readings_plan: Dict = diagnosis["readings_plan"]
    medications: List[Dict] = diagnosis["management_plan"]["doses"]

    # Generate readings based on readings plan.
    reading_days_per_week = int(readings_plan["days_per_week_to_take_readings"])
    readings_per_day = int(readings_plan["readings_per_day"])
    now: datetime = datetime.now(tz=timezone.utc)
    rg = readings_generator.ReadingsGenerator(patient)
    readings: List[Dict] = []
    for i in range(1, days + 1):
        if random.randrange(7) not in range(reading_days_per_week):
            # No readings on this day
            continue
        all_prandial_tags = [1, 2, 3, 4, 5, 6, 7, 7]
        random.shuffle(all_prandial_tags)

        date_start: datetime = now - timedelta(
            days=i,
            hours=now.hour,
            minutes=now.minute,
            seconds=now.second,
            microseconds=now.microsecond,
        )
        for prandial_tag in all_prandial_tags[:readings_per_day]:
            readings.append(
                rg.create_reading(
                    date_start=date_start,
                    prandial_tag=prandial_tag,
                    medication_list=medications,
                )
            )

    # Generate messages based on message probability.
    mg = message_generator.MessageGenerator(patient)
    messages: List[Dict] = []
    if random.random() <= MESSAGE_PROBABILITY and patient.get("locations", []):
        messages = mg.generate_message_data(number_of_messages=1)
        for m in messages:
            # Just let the message be created/modified sometime in the last 24 hours.
            timestamp: datetime = datetime.now(tz=timezone.utc) - timedelta(
                hours=random.randint(0, 24)
            )
            timestamp_iso8601: str = timestamp.isoformat(timespec="milliseconds")
            m["created"] = timestamp_iso8601
            m["modified"] = timestamp_iso8601

    # Generate visits based on visit probability.
    visits: List[Dict] = []
    if random.random() <= VISIT_PROBABILITY and patient.get("locations", []):
        visits.append(
            {
                "visit_date": datetime.now(tz=timezone.utc).isoformat(
                    timespec="milliseconds"
                ),
                "clinician": clinician["uuid"],
                "location": patient["locations"][0],
            }
        )

    if len(readings) == 0 and len(messages) == 0 and len(visits) == 0:
        logger.debug("Generated no new data for this patient, nothing to do")
        return

    # Get a jwt for the patient.
    patient_jwt: str = auth_controller.get_patient_jwt(
        clients=clients, patient_id=patient["uuid"]
    )
    clinician_jwt: str
    if use_system_jwt:
        clinician_jwt = auth_controller.get_system_jwt()
    else:
        clinician_jwt = auth_controller.get_clinician_jwt(
            clinician["email_address"],
            reset_controller.GENERATED_CLINICIAN_PASSWORD,
            clinician_uuid=clinician["uuid"],
        )

    # Readings
    logger.debug(
        "Populating %d readings for patient %s", len(readings), patient["uuid"]
    )
    for reading in readings:
        gdm_bff_client.create_reading(
            clients=clients,
            patient_id=patient["uuid"],
            patient_jwt=patient_jwt,
            reading_details=reading,
        )

    # Messages
    logger.debug("Populating %d messages for patient", len(messages))
    for message in messages:
        # Generate a JWT depending on the message sender.
        if message["sender_type"] == "system":
            message_jwt = auth_controller.get_system_jwt("dhos-robot")
        elif message["sender_type"] == "location":
            message_jwt = clinician_jwt
        elif message["sender_type"] == "patient":
            message_jwt = patient_jwt
        else:
            raise ValueError(
                f"Unexpected message sender type '{message['sender_type']}'"
            )

        messages_client.create_message(
            clients=clients,
            message=message,
            jwt=message_jwt,
            headers={},
        )

    # Visits
    if visits:
        logger.debug(
            "Populating %d visits for patient %s", len(visits), patient["uuid"]
        )
        services_client.update_patient(
            clients=clients,
            patient_id=patient["uuid"],
            patient_details={"record": {"visits": visits}},
            jwt=clinician_jwt,
        )
