import uuid

from behave import register_type, use_fixture, use_step_matcher
from behave.model import Feature, Scenario, Step
from behave.runner import Context
from clients import dhos_client
from clients.wiremock_client import mock_apis
from helpers.users import generate_clinician, generate_patient
from reporting import init_report_portal


def parse_boolean(bool_as_str: str) -> bool:
    return {"true": True, "false": False}[bool_as_str.lower()]


use_step_matcher("cfparse")
register_type(str=str, int=int, float=float, bool=parse_boolean)


def before_tag(context: Context, tag: str) -> None:
    if tag == "fixture.mock.apis":
        use_fixture(mock_apis, context)


def before_all(context: Context) -> None:
    init_report_portal(context)
    # Create dummy patient to deal with an occasional very slow first query.
    location_uuid = str(uuid.uuid4())
    clinician_uuid = dhos_client.post_clinician(
        context=context, clinician=generate_clinician(location_uuid=location_uuid)
    )["uuid"]
    dhos_client.post_patient(
        context=context,
        patient=generate_patient(
            location_uuid=location_uuid, clinician_uuid=clinician_uuid
        ),
    )


def before_feature(context: Context, feature: Feature) -> None:
    context.feature_id = context.behave_integration_service.before_feature(feature)


def before_scenario(context: Context, scenario: Scenario) -> None:
    context.scenario_id = context.behave_integration_service.before_scenario(
        scenario, feature_id=context.feature_id
    )


def before_step(context: Context, step: Step) -> None:
    context.step_id = context.behave_integration_service.before_step(
        step, scenario_id=context.scenario_id
    )


def after_step(context: Context, step: Step) -> None:
    context.behave_integration_service.after_step(step, step_id=context.step_id)


def after_scenario(context: Context, scenario: Scenario) -> None:
    context.behave_integration_service.after_scenario(
        scenario, scenario_id=context.scenario_id
    )


def after_feature(context: Context, feature: Feature) -> None:
    context.behave_integration_service.after_feature(
        feature, feature_id=context.feature_id
    )


def after_all(context: Context) -> None:
    context.behave_integration_service.after_all(launch_id=context.launch_id)
