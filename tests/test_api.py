import pytest
from flask.testing import FlaskClient
from mock import Mock
from pytest_mock import MockFixture

from dhos_janitor_api.blueprint_api.controller import (
    auth_controller,
    populate_controller,
    reset_controller,
)
from dhos_janitor_api.helpers import cache
from dhos_janitor_api.helpers.cache import TaskStatus


class TestApi:
    @pytest.fixture(autouse=True)
    def mock_bearer_validation(self, mocker: MockFixture) -> Mock:
        return mocker.patch(
            "jose.jwt.get_unverified_claims",
            return_value={
                "sub": "1234567890",
                "name": "John Doe",
                "iat": 1_516_239_022,
                "iss": "http://localhost/",
            },
        )

    def test_start_reset_task_success(
        self, client: FlaskClient, mocker: MockFixture
    ) -> None:
        cache.known_tasks = {"uuid1": TaskStatus.COMPLETE, "uuid2": TaskStatus.ERROR}
        mock_start = mocker.patch.object(
            reset_controller,
            "start_reset_thread",
            return_value="task_uuid",
        )
        response = client.post(
            "/dhos/v1/reset_task", headers={"Authorization": f"Bearer TOKEN"}
        )
        assert response.status_code == 202
        assert response.headers["Location"] == "/dhos/v1/task/task_uuid"
        assert mock_start.call_count == 1

    def test_start_reset_task_existing(
        self, client: FlaskClient, mocker: MockFixture
    ) -> None:
        cache.known_tasks = {
            "uuid1": TaskStatus.COMPLETE,
            "uuid2": TaskStatus.RUNNING,
        }
        mock_start = mocker.patch.object(
            reset_controller, "start_reset_thread", return_value="task_uuid"
        )
        response = client.post(
            "/dhos/v1/reset_task", headers={"Authorization": f"Bearer TOKEN"}
        )
        assert response.status_code == 409
        assert mock_start.call_count == 0

    def test_start_populate_task_success(
        self, client: FlaskClient, mocker: MockFixture
    ) -> None:
        cache.known_tasks = {"uuid1": TaskStatus.COMPLETE, "uuid2": TaskStatus.ERROR}
        mock_start = mocker.patch.object(
            populate_controller, "start_populate_gdm_thread", return_value="task_uuid"
        )
        response = client.post(
            "/dhos/v1/populate_gdm_task", headers={"Authorization": f"Bearer TOKEN"}
        )
        assert response.status_code == 202
        assert response.headers["Location"] == "/dhos/v1/task/task_uuid"
        assert mock_start.call_count == 1

    def test_start_populate_task_existing(
        self, client: FlaskClient, mocker: MockFixture
    ) -> None:
        cache.known_tasks = {
            "uuid1": TaskStatus.COMPLETE,
            "uuid2": TaskStatus.RUNNING,
        }
        mock_start = mocker.patch.object(
            populate_controller, "start_populate_gdm_thread", return_value="task_uuid"
        )
        response = client.post(
            "/dhos/v1/reset_task", headers={"Authorization": f"Bearer TOKEN"}
        )
        assert response.status_code == 409
        assert mock_start.call_count == 0

    @pytest.mark.parametrize(
        "task_uuid,expected_status_code",
        [
            ("complete_task_uuid", 200),
            ("running_task_uuid", 202),
            ("error_task_uuid", 400),
        ],
    )
    def test_get_task_success(
        self, client: FlaskClient, task_uuid: str, expected_status_code: int
    ) -> None:
        cache.known_tasks = {
            "complete_task_uuid": TaskStatus.COMPLETE,
            "running_task_uuid": TaskStatus.RUNNING,
            "error_task_uuid": TaskStatus.ERROR,
        }
        response = client.get(
            f"/dhos/v1/task/{task_uuid}",
            headers={"Authorization": f"Bearer TOKEN"},
        )
        assert response.status_code == expected_status_code

    def test_get_clinician_jwt(self, client: FlaskClient, mocker: MockFixture) -> None:
        mock_jwt = mocker.patch.object(
            auth_controller, "get_clinician_jwt", return_value="TOKEN"
        )
        b64userpass = "d29scmFiQG1haWwuY29tOlBhc3NAd29yZDEh"
        response = client.get(
            "/dhos/v1/clinician/jwt", headers={"Authorization": f"Basic {b64userpass}"}
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["access_token"] == "TOKEN"
        assert mock_jwt.call_count == 1

    def test_get_patient_jwt(self, client: FlaskClient, mocker: MockFixture) -> None:
        mock_jwt = mocker.patch.object(
            auth_controller, "get_patient_jwt", return_value="TOKEN"
        )
        response = client.get("/dhos/v1/patient/patient_uuid/jwt")
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["jwt"] == "TOKEN"
        assert mock_jwt.call_count == 1

    def test_get_system_jwt(self, client: FlaskClient, mocker: MockFixture) -> None:
        mock_jwt = mocker.patch.object(
            auth_controller, "get_system_jwt", return_value="TOKEN"
        )
        response = client.get("/dhos/v1/system/dhos-robot/jwt")
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["jwt"] == "TOKEN"
        assert mock_jwt.call_count == 1
