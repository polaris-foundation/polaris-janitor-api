from typing import Optional

from flask import Blueprint, Response, current_app, jsonify, make_response, request
from flask_batteries_included.helpers.error_handler import EntityNotFoundException
from flask_batteries_included.helpers.security import protected_route
from flask_batteries_included.helpers.security.endpoint_security import key_present
from she_logging import logger

from dhos_janitor_api.blueprint_api.client import ClientRepository
from dhos_janitor_api.blueprint_api.controller import (
    auth_controller,
    populate_controller,
    reset_controller,
)
from dhos_janitor_api.helpers import cache
from dhos_janitor_api.helpers.cache import TaskStatus

api_blueprint = Blueprint("api", __name__)


@api_blueprint.route("/dhos/v1/reset_task", methods=["POST"])
@protected_route(key_present("system_id"))
def create_reset_task(
    num_gdm_patients: int,
    num_dbm_patients: int,
    num_send_patients: int,
    num_hospitals: Optional[int] = None,
    num_wards: Optional[int] = None,
) -> Response:
    """---
    post:
      summary: Create reset task
      description: >-
          Drops data from the microservice databases, and repopulates them with
          generated tests data. Passing a list of microservices in the request
          body will reset only those services. Responds with an HTTP 202 and a
          Location header - subsequent HTTP GET requests to this URL will provide
          the status of the task.
      tags: [task]
      parameters:
        - name: num_gdm_patients
          in: query
          required: false
          description: Number of GDM patients to create
          schema:
            type: integer
            default: 12
        - name: num_dbm_patients
          in: query
          required: false
          description: Number of DBM patients to create
          schema:
            type: integer
            default: 18
        - name: num_send_patients
          in: query
          required: false
          description: Number of SEND patients to create
          schema:
            type: integer
            default: 12
        - name: num_hospitals
          in: query
          required: false
          description: Number of hospitals to create
          schema:
            type: integer
            example: 2
        - name: num_wards
          in: query
          required: false
          description: Number of wards to create
          schema:
            type: integer
            example: 2
      requestBody:
        description: JSON body containing the observation set
        required: false
        content:
          application/json:
            schema:
              oneOf:
                - $ref: '#/components/schemas/ResetRequest'
      responses:
        '202':
          description: Reset started
          headers:
            Location:
              description: The location of the created patient
              schema:
                type: string
                example: /dhos/v1/task/2c4f1d24-2952-4d4e-b1d1-3637e33cc161
        '409':
          description: Reset already in progress
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    if not current_app.config["ALLOW_DROP_DATA"]:
        raise PermissionError("Cannot drop data in this environment")

    # Raise a DuplicateResourceException if there's an ongoing task.
    cache.check_no_ongoing_tasks()
    product_settings = {
        "GDM": {"number_of_patients": num_gdm_patients},
        "DBM": {"number_of_patients": num_dbm_patients},
        "SEND": {"number_of_patients": num_send_patients},
    }
    reset_details = request.json if request.is_json else {}
    task_uuid: str = reset_controller.start_reset_thread(
        reset_details=reset_details,
        product_settings=product_settings,
        num_hospitals=num_hospitals,
        num_wards=num_wards,
    )

    response: Response = make_response("", 202)
    response.headers["Location"] = f"/dhos/v1/task/{task_uuid}"
    return response


@api_blueprint.route("/dhos/v1/task/{task_id}", methods=["GET"])
@protected_route(key_present("system_id"))
def get_task(task_id: str) -> Response:
    """---
    get:
      summary: Get task results
      description: >-
          Gets the result of a task by UUID. Responds with either a 202 if the task is ongoing,
          a 200 if it has completed, or a 400 if it has failed.
      tags: [task]
      parameters:
        - name: task_id
          in: path
          required: true
          description: Task UUID
          schema:
            type: string
            example: "bc61563a-2573-48e6-b5c9-1e9a21d06de6"
      responses:
        '200':
          description: Task complete
        '202':
          description: Task ongoing
        '400':
          description: Task error
        default:
          description: >-
              Error, e.g. 404 Not Found, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    logger.info("Getting status of task with UUID %s", task_id)
    logger.debug(
        "%d known tasks",
        len(cache.known_tasks),
        extra={"tasks": {k: str(v) for k, v in cache.known_tasks.items()}},
    )
    if task_id not in cache.known_tasks:
        logger.info("Task %s unknown", task_id)
        raise EntityNotFoundException(f"Task not found with UUID {task_id}")

    status: TaskStatus = cache.known_tasks[task_id]
    if status == TaskStatus.COMPLETE:
        logger.info("Task %s complete", task_id)
        return make_response("", 200)
    if status == TaskStatus.ERROR:
        logger.info("Task %s error", task_id)
        raise ValueError(f"Task with UUID {task_id} has errored")

    # If we got this far, the task still has status RUNNING.
    logger.info("Task %s still running", task_id)
    response: Response = make_response("", 202)
    response.headers["Location"] = f"/dhos/v1/task/{task_id}"
    return response


@api_blueprint.route("/dhos/v1/populate_gdm_task", methods=["POST"])
@protected_route(key_present("system_id"))
def populate_gdm_data(days: int = 1, use_system_jwt: bool = False) -> Response:
    """
    ---
    post:
      summary: Create populate GDM task
      description: >-
        Note: despite the name, this endpoint adds data for both GDM and DBM patients.
        Populate GDM and DBM patients with recent data. Data consists of readings and messages. You can configure
        the number of recent days you want to add data for using the (optional) query parameter; 1 means
        generate data for yesterday, 2 means yesterday and the day before, etc. Responds with an HTTP 202 and a
          Location header - subsequent HTTP GET requests to this URL will provide the status of the task.
      tags: [task]
      parameters:
        - name: days
          in: query
          required: false
          description: The number of recent days for which to populate data
          schema:
            type: integer
            default: 1
        - name: use_system_jwt
          in: query
          required: false
          description: Use a system jwt to populate the additional data
          schema:
            type: boolean
            default: false
      responses:
        '202':
          description: Reset started
          headers:
            Location:
              description: The location of the created patient
              schema:
                type: string
                example: /dhos/v1/task/2c4f1d24-2952-4d4e-b1d1-3637e33cc161
        '409':
          description: Reset already in progress
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    # Raise a DuplicateResourceException if there's an ongoing task.
    cache.check_no_ongoing_tasks()

    task_uuid: str = populate_controller.start_populate_gdm_thread(
        days=days, use_system_jwt=use_system_jwt
    )

    response: Response = make_response("", 202)
    response.headers["Location"] = f"/dhos/v1/task/{task_uuid}"
    return response


@api_blueprint.route("/dhos/v1/clinician/jwt", methods=["GET"])
def get_clinician_jwt(use_auth0: bool = False) -> Response:
    """---
    get:
      summary: Get clinician JWT
      description: Retrieve a clinician JWT from Auth0.
      tags: [jwt]
      parameters:
        - name: Authorization
          in: header
          required: true
          description: Basic authorization header with b64-encoded username:password
          schema:
            type: string
            example: "Basic d29scmFiQG1haWwuY29tOlBhc3NAd29yZDEh"
        - name: use_auth0
          in: query
          required: false
          description: Make request to Auth0 to retrieve JWT if set to `true`; Otherwise, generate JWT locally.
          schema:
            type: boolean
            default: false
      responses:
        '200':
          description: JWT response
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                    description: a valid JWT
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    auth_header = request.headers.get("Authorization", None)
    username, password = auth_controller.get_auth_from_b64_basic_auth(auth_header)
    clinician_jwt: str = auth_controller.get_clinician_jwt(
        username, password, use_auth0=use_auth0
    )
    return jsonify({"access_token": clinician_jwt})


@api_blueprint.route("/dhos/v1/patient/<patient_id>/jwt", methods=["GET"])
def get_patient_jwt(patient_id: str) -> Response:
    """---
    get:
      summary: Get patient JWT
      description: >-
          Retrieve a patient JWT from Activation Auth API. Involves creation of a patient activation,
          and validation of that activation.
      tags: [jwt]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: "55b283e4-a916-4c9c-8986-d75d96996960"
      responses:
        '200':
          description: JWT response
          content:
            application/json:
              schema:
                type: object
                properties:
                  jwt:
                    type: string
                    description: a valid JWT
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(
        {
            "jwt": auth_controller.get_patient_jwt(
                clients=ClientRepository.from_app(current_app),
                patient_id=patient_id,
            )
        }
    )


@api_blueprint.route("/dhos/v1/system/<system_id>/jwt", methods=["GET"])
def get_system_jwt(system_id: str) -> Response:
    """---
    get:
      summary: Get system JWT
      description: >-
          Retrieve a system JWT from System Auth API
      tags: [jwt]
      parameters:
        - name: system_id
          in: path
          required: true
          description: System identifier
          schema:
            type: string
            example: "dhos-robot"
      responses:
        '200':
          description: JWT response
          content:
            application/json:
              schema:
                type: object
                properties:
                  jwt:
                    type: string
                    description: a valid JWT
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    system_jwt: str = auth_controller.get_system_jwt(system_id)
    return jsonify({"jwt": system_jwt})
