"""Flask error classes and handlers
"""
import json
import requests

import toolz
from flask import Response, abort
from werkzeug.exceptions import HTTPException

from app.api import api_bp, api_utils
from app.logger import logger


class ServerError(Exception):
    """Base server error class
    Use this when creating any new types of API errors.
    """
    def __init__(self, code: int, hint: str = None,
                 description: str = None, message: str = None):
        Exception.__init__(self)
        self.code = code
        self.hint = hint
        self.description = description
        self.message = message
        self.error_body_template = {
            "hint": None,
            "code": self.code,
            "description": None,
            "message": None
        }
        self.c_error_details = self.custom_error_details(self.hint,
                                                         self.description,
                                                         self.message)
        self.h_error_details = self.http_error_details(self.code)
        self.error_body = self.create_error_body(self.error_body_template,
                                                 self.c_error_details,
                                                 self.h_error_details)

    @staticmethod
    def custom_error_details(hint: str, description: str, message: str) -> dict:
        """Create a dict of custom error body description.

        Args:
            hint (str): Hint about why the error happened.
            description (str): Description about the error message.
            message (str): Error message.

        Returns:
            dict: Custom error body.
        """
        intermediate = {
            "hint": hint,
            "description": description,
            "message": message,
        }
        return {key: val for key, val in intermediate.items() if val is not None}

    @staticmethod
    def http_error_details(status_code: int) -> dict:
        """Extract error details from standard HTTP error.

        Args:
            status_code (int): Status code.

        Returns:
            dict: Error details.
        """
        try:
            abort(status_code)
        except HTTPException as err:
            return {
                "code": err.code,
                "message": err.name,
                "description": err.description
            }

        # This will never happen, its just here to make linting happy.
        return {}

    @staticmethod
    def create_error_body(error_body_template: dict,
                          h_error_details: dict, c_error_details: dict) -> dict:
        """Create the error body that can be used to send to the client.

        Args:
            error_body_template (dict): Error body template.
            h_error_details (dict): HTTP error details based on the status code.
            c_error_details (dict): Custom error details based on args passed to this class.

        Returns:
            dict: Error body.
        """
        return {
            **error_body_template,
            **h_error_details,
            **c_error_details
        }


class PostgrestHTTPException(ServerError):
    """Used to handle any PostgREST error responses.
    This class will be sent to a Flask error handler that will provide a clean JSON error
    response back to the client.
    """

    def __init__(self, response: requests.Response, hint: str = None,
                 description: str = None, message: str = None):
        super().__init__(response.status_code, hint, description, message)
        logger.error(
            f"[PostgREST] Error {response.status_code} - {response.url}")
        self.response = response
        # NOTE: Maybe this is bad? We are redifining error_body with a new value
        self.error_body = self.postgres_error_details(self.response, self.error_body)

    def __str__(self):
        return f"PostgREST {self.response.status_code} Error"

    @staticmethod
    def postgres_error_details(resp: requests.Response, error_body: dict) -> dict:
        """Create the error body that can be used to send to the client.

        Args:
            resp (requests.Response): Error response.
            error_body_template (dict): Error body template.

        Returns:
            dict: Error body.
        """
        content_type = resp.headers.get('content-type', None)
        json_content_types = [
            "application/vnd.pgrst.object+json; charset=utf-8",
            "application/vnd.pgrst.object+json",
            "application/json; charset=utf-8",
            "application/json"
        ]

        if content_type not in json_content_types:
            # If the content type is not JSON, return generic HTTP error details.
            return error_body

        postgrest_error_response = resp.json()
        message = postgrest_error_response["message"]
        details = postgrest_error_response["details"]
        return {
            **error_body,
            "hint": details,
            "message": message
        }


@api_bp.errorhandler(ServerError)
def handle_server_error_httpexception(err: ServerError) -> Response:
    """Catches ServerError when it is raised and
    creates a JSON response to send to the client.

    Args:
        err (ServerError): ServerError HTTP Exception Class.

    Returns:
        Response: Flask response.
    """
    content = json.dumps(err.error_body)
    status_code = err.code

    headers = {
        "Content-Type": "application/json"
    }
    return Response(content, status_code, headers)


@api_bp.errorhandler(PostgrestHTTPException)
def handle_postgrest_httpexception(err: PostgrestHTTPException) -> Response:
    """Catches PostgrestHTTPException when it is raised and
    creates a JSON response to send to the client.

    Args:
        err (PostgrestHTTPException): PostgREST HTTP Exception Class.

    Returns:
        Response: Flask response.
    """
    error_resp = err.response
    status_code = error_resp.status_code
    content = json.dumps(err.error_body)
    headers = api_utils.create_headers(error_resp, {}, status_code)

    return Response(content, status_code, headers)


@api_bp.errorhandler(HTTPException)
def handle_httpexception(err: HTTPException) -> Response:
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = err.get_response()

    try:
        validation_messages = err.data.get("messages", None)
    except AttributeError:
        validation_messages = None

    error_body = ServerError(response.status_code).error_body

    if validation_messages:
        error_body_with_validation_errors = toolz.thread_first(
            error_body,
            # Remove description from dict
            (toolz.dissoc, "description"),
            # Merge other fields into the dict
            lambda x: {
                **x,
                "hint": "Errors with query params",
                "code": err.code,
                "message": "Validation errors",
                "errors": validation_messages
            }
        )
        response.data = json.dumps(error_body_with_validation_errors)
    else:
        response.data = json.dumps(error_body)

    response.content_type = "application/json"
    return response
