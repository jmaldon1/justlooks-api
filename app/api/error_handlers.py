"""Flask error handlers
"""
import json
import requests

from flask import Response, abort
from werkzeug.exceptions import HTTPException

from app.api import api_bp, api_utils


class PostgrestHTTPException(Exception):
    """Used to handle any PostgREST error responses.
    This class will be sent to a Flask error handler that will provide a clean JSON error
    response back to the client.
    """

    def __init__(self, response: requests.Response,
                 hint: str = None, details: str = None, message: str = None):
        Exception.__init__(self)
        self.response = response
        self.hint = hint
        self.details = details
        self.message = message
        self.error_body_template = {
            "hint": None,
            "code": response.status_code,
            "details": None,
            "message": None
        }
        self.error_body = self.create_error_body(self.response,
                                                 self.error_body_template)

    def __str__(self):
        return f"PostgREST {self.response.status_code} Error"

    @staticmethod
    def create_custom_error(hint: str, details: str, message: str) -> dict:
        """Create a dict of custom error body details.

        Args:
            hint (str): Hint about why the error happened.
            details (str): Details about the error message.
            message (str): Error message.

        Returns:
            dict: Custom error body.
        """
        intermediate = {
            "hint": hint,
            "details": details,
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
                                                     self.details,
                                                     self.message)

        error_body = {
            **error_body_template,
            **resp.json(),
            **custom_error_body
        }
        return error_body


@api_bp.errorhandler(PostgrestHTTPException)
def handle_postgrest_httpexception(e: PostgrestHTTPException) -> Response:
    error_resp = e.response
    status_code = error_resp.status_code
    content = json.dumps(e.error_body)
    headers = api_utils.create_headers(error_resp, {}, status_code)

    return Response(content, status_code, headers)


@api_bp.errorhandler(HTTPException)
def handle_exception(e: HTTPException):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "hint": None,
        "details": e.description,
        "code": e.code,
        "message": e.name
    })

    response.content_type = "application/json"
    return response
