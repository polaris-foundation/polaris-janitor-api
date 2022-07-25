import asyncio
import time

from behave import step, then, when
from behave.api.async_step import async_run_until_complete
from behave.runner import Context
from clients.dhos_client import (
    database_reset,
    get_all_patients_fuego,
    is_task_completed,
    patient_search_fuego,
    populate_gdm_data,
    search_patients,
)


@when(
    "the database has been reset with {gdm_patients:int} GDM, {dbm_patients:int} DBM, "
    "and {send_patients:int} SEND patients"
)
def database_reset_step(
    context: Context, gdm_patients: int, dbm_patients: int, send_patients: int
) -> None:
    context.task_name = "database reset"
    database_reset(
        context,
        num_gdm_patients=gdm_patients,
        num_dbm_patients=dbm_patients,
        num_send_patients=send_patients,
        num_hospitals=1,
        num_wards=2,
    )


@then("the running task completes within {duration:float} seconds")
@async_run_until_complete
async def wait_task_completion_step(context: Context, duration: float) -> None:
    """Simple example of a coroutine as async-step (in Python 3.5 or newer)"""
    start: float = time.time()
    while not is_task_completed(context, context.task_name):
        if time.time() - start > duration:
            break
        await asyncio.sleep(0.5)


@step("the FHIR EPR is populated with GDm patients")
def fhir_epr_is_populated_step(context: Context) -> None:
    gdm_active_patients_with_fhir_resource_id = [
        p for p in search_patients(context, "GDM") if p.get("fhir_resource_id")
    ]

    fuego_all_patients = get_all_patients_fuego(context)

    assert len(fuego_all_patients) == len(gdm_active_patients_with_fhir_resource_id)

    fuego_gdm_active_patients = [
        patient_search_fuego(context, p["hospital_number"])[0]
        for p in gdm_active_patients_with_fhir_resource_id
    ]

    assert len(fuego_gdm_active_patients) == len(
        gdm_active_patients_with_fhir_resource_id
    )

    gdm_active_patients_fhir_resource_id_list = [
        p["fhir_resource_id"] for p in gdm_active_patients_with_fhir_resource_id
    ]

    for fuego_gdm_active_patient in fuego_gdm_active_patients:
        assert (
            fuego_gdm_active_patient["fhir_resource_id"]
            in gdm_active_patients_fhir_resource_id_list
        )


@when("we populate GDM data")
def populate_gdm(context: Context) -> None:
    context.task_name = "populate GDM data"
    populate_gdm_data(context)


@then("patients with static uuids also have static MRNs")
def patients_static_uuid_mrn(context: Context) -> None:
    gdm_patients = search_patients(context, "GDM")

    for p in gdm_patients:
        if not p["uuid"].startswith("static_"):
            continue

        i = p["uuid"].split("_")[-1]
        assert p["hospital_number"] == i * 6
