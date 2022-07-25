import requests
from behave import given, then, when
from behave.runner import Context


@given("dhos-janitor-api has been started")
def api_has_started(context: Context) -> None:
    ...


@when("we fetch from /running")
def fetch_running(context: Context) -> None:
    response = requests.get(url="http://dhos-janitor-api:5000/running")
    context.response = response


@then("the result is 200")
def response_is_ok(context: Context) -> None:
    assert context.response.status_code == 200
