"""PostgREST proxy
"""
import traceback
from functools import partial
from urllib.parse import urljoin

import requests
import toolz
from flask import current_app, request, Response, after_this_request, make_response
from werkzeug.datastructures import ImmutableMultiDict

from app.api import api_bp, api_utils
from app.logger import logger
from app.api.error_handlers import ServerError, PostgrestHTTPException
from app import utils


@api_bp.route('/api/<path:path>', methods=['GET'])
def get_postgrest_proxy(path: str) -> Response:
    """Proxy for PostgREST that modifies various parts of the request,
    such as query params and headers.

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
        aceh_vals = toolz.pipe(
            # Get response Access-Control-Expose-Headers values as list.
            modified_response.headers.getlist("Access-Control-Expose-Headers"),
            # Lowercase all the values.
            lambda l: [x.lower() for x in l]
        )

        if "link" not in aceh_vals and len(aceh_vals) > 0:
            modified_response.headers.extend({"Access-Control-Expose-Headers": "Link"})
        return modified_response

    config = current_app.config['CONFIG']
    postgrest_host = config['postgrest_host']
    postgrest_url = urljoin(postgrest_host, path)

    modified_query_params = modify_query_params(request.args, postgrest_host)

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
            params=modified_query_params
        )
    except requests.exceptions.ConnectionError as err:
        logger.error(traceback.format_exc())
        raise ServerError(503, hint="Could not connect to Postgrest.") from err

    postgrest_status_code = postgrest_resp.status_code
    # Abort if we get an error code.
    if postgrest_status_code >= 300:
        raise PostgrestHTTPException(postgrest_resp)

    # Create new headers
    headers = api_utils.create_headers(postgrest_resp,
                                       modified_query_params,
                                       postgrest_status_code)

    # Create response to send back to client
    response = Response(postgrest_resp.content,
                        postgrest_status_code,
                        headers)

    return response


def modify_query_params(request_query_params: ImmutableMultiDict, host_url: str) -> dict:
    """Enhance the query params that the client provided to us.

    Args:
        request_query_params (ImmutableMultiDict): Flask query params.
        host_url (str): Host url that the proxy will be sending all requests too.

    Returns:
        dict: Modified query params.
    """
    raw_request_query_params = request_query_params.to_dict(flat=False)
    return toolz.pipe(raw_request_query_params,
                      utils.replace_single_len_lists,
                      api_utils.add_default_sorting,
                      partial(api_utils.create_pivot_value_request_param,
                              postgrest_host=host_url))
