from time import sleep
from typing import Any, Dict, NoReturn

import pytest
from flask import Flask, Response

from dhos_janitor_api.blueprint_api import ClientRepository
from dhos_janitor_api.blueprint_api.janitor_thread import JanitorTarget, JanitorThread

WAIT_TIME = 0.1


class SpecificException(Exception):
    ...


@pytest.mark.usefixtures("app")
class TestJanitorThread:
    def _mock_thread(
        self,
        clients: ClientRepository,
    ) -> Dict:
        sleep(WAIT_TIME)
        return {"some": "thing"}

    def _mock_failed_thread(
        self,
        clients: ClientRepository,
    ) -> NoReturn:
        sleep(WAIT_TIME)
        raise SpecificException("nope")

    def _mock_app(self, app: Flask, target: JanitorTarget) -> Any:
        @app.route("/")
        def _route() -> Response:
            thread = JanitorThread(
                task_uuid="task_uuid", target=target, request_id="some-request-id"
            )
            thread.start()
            # for some reason, stream_with_context doesn't work with test client
            response_string = "".join(thread.wait_for_response()).strip()
            return Response(
                response_string, status=200, content_type="application/json"
            )

        client = app.test_client()
        return client.get("/")  # no timeout kwarg :(

    def test_returns_response(self, app: Flask) -> None:
        with app.app_context():
            thread = JanitorThread(
                task_uuid="task_uuid",
                target=self._mock_thread,
                request_id="some-request-id",
            )
            thread.start()
            responses = [i for i in thread.wait_for_response()]
        assert all(r == "\n" for r in responses[:-1])
        assert responses[-1] == '{"some": "thing"}'

    def test_stream_response(self, app: Flask) -> None:
        response = self._mock_app(app, self._mock_thread)
        assert response.status_code == 200
        assert response.json == {"some": "thing"}

    def test_handles_error(self, app: Flask) -> None:
        with pytest.raises(SpecificException):
            self._mock_app(app, self._mock_failed_thread)

    def test_raises_error_if_already_open(self, app: Flask) -> None:
        with app.app_context(), pytest.raises(RuntimeError):
            thread = JanitorThread(
                task_uuid="task_uuid",
                target=self._mock_thread,
                request_id="some-request-id",
            )
            thread.start()
            thread.start()

    def test_raises_error_if_not_open(self, app: Flask) -> None:
        with app.app_context(), pytest.raises(RuntimeError):
            thread = JanitorThread(
                task_uuid="task_uuid",
                target=self._mock_thread,
                request_id="some-request-id",
            )
            for _ in thread.wait_for_response():
                ...
