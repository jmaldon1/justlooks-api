"""Flask error handlers
"""
import json
import requests
from typing import Optional

import toolz
from flask import Response, abort
from werkzeug.exceptions import HTTPException

from app.api import api_bp, api_utils
from app.logger import logger


ERROR_BODY_TEMPLATE = {
    "hint": None,
    "code": None,
    "description": None,
    "message": None
}


class PostgrestHTTPException(Exception):
    """Used to handle any PostgREST error responses.
    This class will be sent to a Flask error handler that will provide a clean JSON error
    response back to the client.
    """

    def __init__(self, response: requests.Response, hint: str = None,
                 description: str = None, message: str = None):
        Exception.__init__(self)
        logger.error(
            f"[PostgREST] Error {response.status_code} - {response.url}")
        self.response = response
        self.hint = hint
        self.description = description
        self.message = message
        self.error_body_template = {
            **ERROR_BODY_TEMPLATE, "code": response.status_code}
        self.error_body = self.create_error_body(self.response,
                                                 self.error_body_template)

    def __str__(self):
        return f"PostgREST {self.response.status_code} Error"

    @staticmethod
    def create_custom_error(hint: str, description: str, message: str) -> dict:
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

    def create_error_body(self, resp: requests.Response, error_body_template: dict) -> dict:
        """Create the error body that can be used to send to the client.

        Args:
            resp (requests.Response): Error response.
            error_body_template (dict): Error body template.

        Returns:
            dict: Error body.
        """
        status_code = resp.status_code
        content_type = resp.headers.get('content-type')
        json_content_types = [
            "application/vnd.pgrst.object+json; charset=utf-8",
            "application/vnd.pgrst.object+json",
            "application/json; charset=utf-8",
            "application/json"
        ]

        if content_type not in json_content_types:
            # If the content type is not JSON, raise a generic HTTP exception
            abort(status_code)

        custom_error_body = self.create_custom_error(self.hint,
                                                     self.description,
                                                     self.message)

        error_body = {
            **error_body_template,
            **resp.json(),
            **custom_error_body
        }
        return error_body


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
def handle_exception(err: HTTPException) -> Response:
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = err.get_response()

    validation_messages = err.data.get("messages", None)

    err_body = create_error_body(err, ERROR_BODY_TEMPLATE, validation_messages)
    # replace the body with JSON
    response.data = json.dumps(err_body)

    response.content_type = "application/json"
    return response


def create_error_body(err: HTTPException, error_body_template: dict,
                      validation_messages: Optional[list] = None) -> dict:
    """Create an error body that depends on validation errors

    Args:
        err (HTTPException): HTTP Error.
        validation_messages (Optional[list], optional): Validation Errors. Defaults to None.

    Returns:
        dict: Error body.
    """
    if validation_messages:
        modified_error_body_template = toolz.dissoc(
            error_body_template, "description")
        return {
            **modified_error_body_template,
            "code": err.code,
            "message": "Validation Errors",
            "errors": validation_messages
        }

    return {**error_body_template, "description": err.description}
