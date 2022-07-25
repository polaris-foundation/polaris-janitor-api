from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask_batteries_included.helpers.apispec import (
    FlaskBatteriesPlugin,
    initialise_apispec,
    openapi_schema,
)
from marshmallow import EXCLUDE, Schema, fields

dhos_janitor_api_spec: APISpec = APISpec(
    version="1.0.0",
    openapi_version="3.0.3",
    title="DHOS Janitor API",
    info={
        "description": "The DHOS Janitor API is responsible for managing data in non-production environments."
    },
    plugins=[FlaskPlugin(), MarshmallowPlugin(), FlaskBatteriesPlugin()],
)

initialise_apispec(dhos_janitor_api_spec)


@openapi_schema(dhos_janitor_api_spec, {"nullable": True})
class ResetRequest(Schema):
    class Meta:
        title = "Reset request"
        unknown = EXCLUDE
        ordered = True

    targets = fields.List(fields.String(), description="List of services to reset")
