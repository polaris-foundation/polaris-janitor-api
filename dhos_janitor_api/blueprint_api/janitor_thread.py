import contextlib
import json
import sys
import threading
import time
from typing import Any, Callable, Dict, Iterator, NoReturn, Optional, Union

import flask
from flask import Flask
from she_logging import logger
from she_logging.request_id import set_request_id

from dhos_janitor_api.blueprint_api.client import ClientRepository
from dhos_janitor_api.helpers import cache
from dhos_janitor_api.helpers.cache import TaskStatus

JanitorTarget = Callable[..., Union[Dict, None, NoReturn]]


class JanitorThread:
    """
    Class for running a task on a separate thread.
    """

    _name = "janitor thread"
    _keep_alive_interval = 0.5

    _task_uuid: str
    _request_id: Optional[str]
    _is_open: bool
    _response: Any
    _started: float
    _require_context: bool
    _app: Flask

    def __init__(
        self,
        task_uuid: str,
        target: JanitorTarget,
        request_id: Optional[str],
        require_context: bool = False,
    ) -> None:
        """
        :param target: Target callable to be run on a thread
        :param require_context: Should the call to 'target' be wrapped in app_context?
        """
        self._task_uuid = task_uuid
        self._request_id = request_id
        self._target: JanitorTarget = target
        self._is_open = False
        self._response = None
        self._started = -1
        self._require_context = require_context
        self._app = flask.current_app._get_current_object()
        self._clients = ClientRepository.from_app(self._app)

    @contextlib.contextmanager
    def _context(self) -> Iterator[Any]:
        """
        Yields context from current app if '_require_context' is True,
        otherwise yields None
        """
        try:
            if self._require_context:
                logger.info("getting app context for %s", self._name)
                yield self._app.app_context()
            else:
                yield
        except Exception:
            raise

    def start(self, **kwargs: Any) -> None:
        """
        Runs '_target' as a thread.

        Raises RuntimeError if the thread is already running

        NOTE: app (flask.Flask) is implicitly passed to the target as the first argument
        """
        if self._is_open:
            cache.known_tasks[self._task_uuid] = TaskStatus.ERROR
            raise RuntimeError(f"thread '{self._name}'' is already running")
        self._is_open = True
        self._started = time.time()
        thread: threading.Thread = threading.Thread(target=self._run, kwargs=kwargs)
        logger.info("starting %s (ID %s)", self._name, self._task_uuid)
        cache.known_tasks[self._task_uuid] = TaskStatus.RUNNING
        thread.start()

    def wait_for_response(
        self, encoder: Callable[[Any], str] = json.dumps
    ) -> Iterator[str]:
        """
        Checks the thread at intervals to see if it has finished.

        If it is still open, an empty string is yielded,
        otherwise the return object is encoded and yielded.
        """

        if not self._is_open:
            cache.known_tasks[self._task_uuid] = TaskStatus.ERROR
            raise RuntimeError(f"thread {self._name} is not running")

        logger.info("waiting for response from %s (ID %s)", self._name, self._task_uuid)

        while self._is_open:
            logger.info(
                "still waiting for response from %s (ID %s)...",
                self._name,
                self._task_uuid,
            )
            yield "\n"
            time.sleep(self._keep_alive_interval)

        logger.info("got response from %s (ID %s)", self._name, self._task_uuid)
        response = self._response or {}

        if isinstance(response, Exception):
            cache.known_tasks[self._task_uuid] = TaskStatus.ERROR
            logger.exception(
                "%s (ID %s) returned an exception",
                self._name,
                self._task_uuid,
                exc_info=response,
            )
            raise response  # for some reason, logger.exception doesn't re-raise in unit tests

        yield encoder(response)

    def _run(self, **kwargs: Any) -> None:
        try:
            if self._request_id:
                set_request_id(self._request_id)
            with self._context():
                self._response = self._target(clients=self._clients, **kwargs)
            cache.known_tasks[self._task_uuid] = TaskStatus.COMPLETE
            logger.info(
                "%s (ID %s) complete after %d seconds",
                self._name,
                self._task_uuid,
                int(time.time() - self._started),
            )
        except Exception as ex:
            cache.known_tasks[self._task_uuid] = TaskStatus.ERROR
            logger.exception(
                "%s (ID %s) failed after %s seconds\n%s",
                self._name,
                self._task_uuid,
                time.time() - self._started,
                ex.with_traceback(sys.exc_info()[2]),
            )
            self._response = ex
        finally:
            logger.info("closing %s (ID %s)", self._name, self._task_uuid)
            self._is_open = False
