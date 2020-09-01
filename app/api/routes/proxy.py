"""PostgREST proxy
"""
import traceback
from functools import partial
from urllib.parse import urljoin

import requests
import toolz
from flask import current_app, request, Response, after_this_request, make_response

from app.api import api_bp, api_utils
from app.logger import logger
from app.api.error_handlers import ServerError, PostgrestHTTPException
from app import utils


@api_bp.route('/api/<path:path>', methods=['GET'])
def get_postgrest_proxy(path: str) -> Response:
    """Proxy for PostgREST that modifies various parts of the request,
    such as request params and headers.

    Args:
        path (str): URL path that corresponds to a PostgREST route

    Returns:
        Response: Flask response that mimicks the PostgREST response.
    """
    @after_this_request
    def __add_cors_link_header(response: Response) -> Response:
        """Adds CORS Link header to the response if it does not already exist.
        This function is run after the outside function is returned.
        https://werkzeug.palletsprojects.com/en/1.0.x/datastructures/#werkzeug.datastructures.Headers

        Args:
            response (Response): Flask response.

        Returns:
            Response: Flask response with CORS Link headers.
        """
        modified_response = make_response(response)
        aceh_vals = modified_response.headers.getlist("Access-Control-Expose-Headers")
        if "Link" not in aceh_vals and len(aceh_vals) > 0:
            modified_response.headers.extend({"Access-Control-Expose-Headers": "Link"})
        return modified_response

    config = current_app.config['CONFIG']
    postgrest_host = config['postgrest_host']

    # Modify query params
    raw_request_params = request.args.to_dict(flat=False)

    postgrest_url = urljoin(postgrest_host, path)
    request_params = toolz.pipe(raw_request_params,
                                utils.replace_single_len_lists,
                                api_utils.add_default_sorting,
                                partial(api_utils.create_pivot_value_request_param,
                                        postgrest_host=postgrest_host))

    # Send PostgREST the same request we received but with modified query params
    try:
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
    except requests.exceptions.ConnectionError:
        logger.error(traceback.format_exc())
        raise ServerError(503, hint="Could not connect to Postgrest.")

    postgrest_status_code = postgrest_resp.status_code

    # Abort if we get an error code.
    if postgrest_status_code >= 300:
        raise PostgrestHTTPException(postgrest_resp)

    # Create new headers
    headers = api_utils.create_headers(postgrest_resp,
                                       request_params,
                                       postgrest_status_code)

    # Create response to send back to client
    response = Response(postgrest_resp.content,
                        postgrest_status_code,
                        headers)

    return response
