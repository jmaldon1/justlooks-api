"""Functions here will be performed after any request.
"""
from flask import Response, make_response

from app.api import api_bp


@api_bp.after_request
def add_cors_headers(response: Response) -> Response:
    """This will execute after any request in this Blueprint. It will extend
    the headers of the current response.
    https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.make_response

    https://blog.container-solutions.com/a-guide-to-solving-those-mystifying-cors-issues

    Args:
        response (Response): Outgoing flask response.

    Returns:
        Response: Response with CORS headers.
    """
    modified_response = make_response(response)
    # If Access-Control-Allow-Origin header is not there, set it.
    modified_response.headers.setdefault("Access-Control-Allow-Origin", "*")
    return modified_response
