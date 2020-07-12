"""PostgREST proxy
"""
from functools import partial
from urllib.parse import urljoin
import json
import requests
import toolz

from flask import current_app, request, Response

from app.api import api_bp, api_utils
from app.api.error_handlers import PostgrestHTTPException
from app import utils
from app.logger import logger


@api_bp.route('/<path:path>', methods=['GET'])
def get_postgrest_proxy(path: str) -> Response:
    """Proxy for PostgREST that modifies various parts of the request,
    such as request params and headers.

    Args:
        path (str): URL path that corresponds to a PostgREST route

    Returns:
        Response: Flask response that mimicks the PostgREST response.
    """
    config = current_app.config['CONFIG']
    postgrest_host = config['postgrest_host']

    # Modify query params
    raw_request_params = request.args.to_dict(flat=False)

    postgrest_url = urljoin(postgrest_host, path)
    request_params = toolz.pipe(raw_request_params,
                                utils.replace_single_len_lists,
                                api_utils.add_default_sorting,
                                partial(api_utils.add_pivot_value,
                                        url=postgrest_url))

    # Send PostgREST the same request we received but with modified query params
    postgrest_resp = requests.request(
        method=request.method,
        url=postgrest_url,
        headers={key: value for (key, value)
                 in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        params=request_params
    )

    postgrest_status_code = postgrest_resp.status_code

    # Create new headers
    headers = api_utils.create_headers(postgrest_resp,
                                       request_params,
                                       postgrest_status_code)

    # Create response to send back to client
    response = Response(postgrest_resp.content,
                        postgrest_status_code,
                        headers)

    # Abort if we get an error code.
    if postgrest_status_code >= 300:
        logger.error(f"PostgREST returned a {postgrest_status_code} error.")
        raise PostgrestHTTPException(response)

    return response
