from functools import partial
import json
import re
from urllib.parse import urlencode, urlparse, urlunparse, urljoin
import requests
import toolz

from flask import current_app, request, Response, abort
from werkzeug.exceptions import HTTPException

from app.api import api_bp
from app import utils
from app.logger import logger


def format_requests(request_params: dict) -> dict:
    return {key: utils.remove_single_length_lists(val) for key, val in request_params.items()}


def add_default_sorting(request_params: dict, default_sort: str = "int_id") -> dict:
    sort = request_params.get("order", None)
    if sort:
        sort_columns = sort.split(",")
        # Check if the `default_sort` is being sorted on already
        if not any(default_sort in col for col in sort_columns):
            # If there is a sort but no default sort, add the default sort
            modified_sort_columns = sort_columns + [default_sort]
            modified_sort = ",".join(modified_sort_columns)
            return {**request_params, "order": modified_sort}

        # If `default_sort` is already in the sort, leave it
        return request_params

    # If there is no sort, add the default sort
    return {**request_params, "order": default_sort}


def add_pivot_value(request_params: dict, postgrest_host: str) -> dict:
    """Find the pivot value for a seek pagination.
    This should only happen if the user is sorting by anything other than `int_id`,
    and want to get data after a certain `int_id`.

    Args:
        request_params (dict): [description]
        postgrest_host (str): [description]

    Returns:
        dict: [description]
    """
    try:
        split_sort = request_params['order'].split(",")
        int_id_q = request_params.get('int_id', None)
        split_int_id_q = int_id_q.split(".")
    except AttributeError:
        return request_params

    if split_sort[0] != "int_id" and split_int_id_q[0] == "gt":
        sort_col = split_sort[0]
        try:
            int_id = int(split_int_id_q[1])
        except ValueError:
            print("Could not get int_id.")
            return request_params

        pivot_request_params = {
            "int_id": f"eq.{int_id}",
            "select": sort_col
        }

        resp = requests.get(f'{postgrest_host}/products',
                            params=pivot_request_params)
        results = resp.json()
        if results:
            pivot_value = results[0][sort_col]

            return {**request_params, sort_col: f"gte.{pivot_value}"}

    return request_params


def create_headers(resp: requests.Response, request_params: dict, status_code: int) -> dict:
    # Remove excluded headers
    excluded_headers = ['content-encoding', 'transfer-encoding']
    headers = {name: val for name, val in resp.raw.headers.items(
    ) if name.lower() not in excluded_headers}

    if status_code != 200:
        return headers

    assert "Content-Range" in headers, "Content-Range is missing from header?"
    content_range_header = headers['Content-Range']

    # if _ is assigned, it will be the total length of the response
    response_len, _ = content_range_header.split("/")
    response_range = re.findall(r'\d+', response_len)
    if not response_range:
        return headers

    response_range_int = [int(i) for i in response_range]
    total_range = (response_range_int[1] - response_range_int[0]) + 1

    limit_q = request_params.get("limit", None)
    try:
        limit = int(limit_q)
    except (TypeError, ValueError):
        # No limit found, just return
        return headers

    results = resp.json()
    if results and total_range == limit:
        # When do we create a next link header?
        #   1. If results has data
        #   2. If the Content-Range is equal to the limit in the query
        #       ex. Content-Range=0-9/* and limit=10
        last_id = results[-1]["int_id"]
        link_header = create_next_link_header(last_id, request_params)
        return {**headers, "Link": link_header}

    return headers


def create_next_link_header(last_id: int, request_params: dict) -> dict:
    next_page_params = {**request_params, "int_id": f"gt.{last_id}"}

    request_url = request.url
    next_page_params_encoded = urlencode(next_page_params)

    next_request_url = toolz.pipe(request_url,
                                  urlparse,
                                  lambda req_url: req_url._replace(
                                      query=next_page_params_encoded),
                                  urlunparse)

    link_header = f'<{next_request_url}>; rel="next"'

    return {"Link": link_header}


@api_bp.route('/<path:path>', methods=['GET'])
def get_postgrest_proxy(path):
    config = current_app.config['CONFIG']
    postgrest_host = config['postgrest_host']

    # Modify query params
    raw_request_params = request.args.to_dict(flat=False)
    request_params = toolz.pipe(raw_request_params,
                                format_requests,
                                add_default_sorting,
                                partial(add_pivot_value,
                                        postgrest_host=postgrest_host))

    # Send postgrest the same request we received but with modified query params
    postgrest_resp = requests.request(
        method=request.method,
        url=urljoin(postgrest_host, path),
        headers={key: value for (key, value)
                 in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        params=request_params
    )

    postgrest_status_code = postgrest_resp.status_code

    # Create new headers
    headers = create_headers(postgrest_resp,
                             request_params,
                             postgrest_status_code)

    # Create response to send back to client
    response = Response(postgrest_resp.content,
                        postgrest_status_code,
                        headers)

    # Abort if we get an error code.
    error_codes = [404]
    if postgrest_status_code in error_codes:
        logger.error(f"PostgREST returned a {postgrest_status_code} error.")
        abort(postgrest_status_code)

    return response


@api_bp.errorhandler(HTTPException)
def handle_exception(e):
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
