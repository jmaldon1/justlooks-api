from flask import Response, make_response

from app.api import api_bp


@api_bp.after_request
def add_cors_headers(response: Response) -> Response:
    """This will execute after any request in this Blueprint. It will extend
    the headers of the current response.
    https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.make_response
    Any headers placed in `extended_headers` will be extended into the current headers.

    https://blog.container-solutions.com/a-guide-to-solving-those-mystifying-cors-issues

    Args:
        response (Response): Outgoing flask response.

    Returns:
        Response: Response with CORS.
    """
    # extended_headers = {
    #     "Access-Control-Expose-Headers": "Link",
    # }
    # # https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.make_response
    # # Any headers placed above will be extended onto the current headers.
    # return make_response(response, extended_headers)
    return response
