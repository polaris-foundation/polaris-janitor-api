from pathlib import Path

import pytest
import yaml
from flask import Flask
from flask_batteries_included import init_metrics, init_monitoring


@pytest.mark.usefixtures("app")
def test_openapi(tmp_path: str, app: Flask) -> None:
    from flask_batteries_included.helpers.apispec import generate_openapi_spec

    from dhos_janitor_api.blueprint_api import api_blueprint
    from dhos_janitor_api.models.api_spec import dhos_janitor_api_spec

    # Add the metrics paths to the app
    init_monitoring(app)
    init_metrics(app)
    new_spec_path = Path(tmp_path) / "testapi.yaml"

    generate_openapi_spec(dhos_janitor_api_spec, new_spec_path, api_blueprint)

    new_spec = yaml.safe_load(new_spec_path.read_bytes())
    existing_spec = Path(__file__).parent / "../dhos_janitor_api/openapi/openapi.yaml"
    existing = yaml.safe_load(existing_spec.read_bytes())

    assert existing == new_spec
