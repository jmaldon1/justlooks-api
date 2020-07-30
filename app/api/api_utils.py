"""Utility functions that are used in API requests
"""
from urllib.parse import urlencode, urlunparse, urlparse, urljoin
import re
import toolz
import requests

from flask import request

from app.logger import logger
from app.api.error_handlers import PostgrestHTTPException


def add_default_sorting(request_params: dict, default_sort: str = "int_id") -> dict:
    """Add a default sorting on all requests sent through the API.

    Args:
        request_params (dict): Request params.
        default_sort (str, optional): Column to sort on. Defaults to "int_id".

    Returns:
        dict: Requests params with sort applied.
    """
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


def create_pivot_value_request_param(request_params: dict, postgrest_host: str) -> dict:
    """Find the pivot value for a seek pagination.
    This should only happen if the user is sorting by anything other than `int_id`,
    and wants to get data after a certain `int_id`.
    NOTE: This function performs an O(1) SELECT to find the pivot value.

    Args:
        request_params (dict): Original request params
        postgrest_host (str): URL to PostgREST

    Returns:
        dict: Request params with pivot value added
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
            logger.debug("Could not get int_id.")
            return request_params

        pivot_value_payload = {
            "int_id": int_id,
            "col": sort_col
        }
        resp = requests.post(urljoin(postgrest_host, "rpc/pivot_value"),
                             data=pivot_value_payload)

        if resp.status_code >= 300:
            raise PostgrestHTTPException(resp)

        pivot_value = resp.json()
        if pivot_value:
            return {**request_params, sort_col: f"gte.{pivot_value}"}

    return request_params


def create_headers(resp: requests.Response, request_params: dict, status_code: int) -> dict:
    """Create various customer headers that need to be added to a PostgREST response.

    Args:
        resp (requests.Response): PostgREST response.
        request_params (dict): Request params.
        status_code (int): Status code of the PostgREST response.

    Returns:
        dict: Headers.
    """
    # Remove excluded headers
    excluded_headers = ['content-encoding', 'transfer-encoding']
    headers = {name: val for name, val in resp.raw.headers.items(
    ) if name.lower() not in excluded_headers}

    if status_code >= 300:
        return headers

    assert "Content-Range" in headers, "Content-Range is missing from header?"
    content_range_header = headers['Content-Range']

    link_header = create_link_header(resp,
                                     request_params,
                                     content_range_header)

    # https://blog.container-solutions.com/a-guide-to-solving-those-mystifying-cors-issues
    return {
        **headers,
        **link_header,
        "Access-Control-Expose-Headers": "*"
    }


def create_link_header(resp: requests.Response, request_params: dict,
                       content_range_header: str) -> dict:
    """Create the link header that will provide pagination for the client.

    Args:
        resp (requests.Response): PostgREST response.
        request_params (dict): Request params.
        content_range_header (dict): Content-Range header from postgREST.

    Returns:
        dict: Link header.
    """
    link_header = []

    limit_q = request_params.get("limit", None)
    try:
        limit = int(limit_q)
    except (TypeError, ValueError):
        # No limit found, just return
        return {}

    try:
        # if _ is assigned, it will be the total length of the response
        response_len, _ = content_range_header.split("/")
        response_range = re.findall(r'\d+', response_len)
        response_range_int = [int(i) for i in response_range]
        total_range = (response_range_int[1] - response_range_int[0]) + 1
    except IndexError:
        # This will happen if we can't find a number value in the Content-Range header
        return {}

    results = resp.json()
    if results and total_range == limit:
        # When do we create a next link header?
        #   1. If results has data
        #   2. If the Content-Range is equal to the limit in the query
        #       ex. Content-Range=0-9/* and limit=10
        last_item = results[-1]
        last_id = last_item.get("int_id", None)
        if last_id:
            last_id = results[-1]["int_id"]
            next_link = create_next_link_header(last_id, request_params)
            link_header.append(next_link)

    if link_header:
        " ".join(link_header)
        return {"Link": link_header}

    return {}


def create_next_link_header(last_id: int, request_params: dict) -> str:
    """Create the next link header.

    Args:
        last_id (int): `int_id` of the last item returned in the current request.
        request_params (dict): Request params.

    Returns:
        str: Next link.
    """
    next_page_params = {**request_params, "int_id": f"gt.{last_id}"}

    request_url = request.url
    next_page_params_encoded = urlencode(next_page_params)

    next_request_url = toolz.pipe(request_url,
                                  urlparse,
                                  lambda req_url: req_url._replace(
                                      query=next_page_params_encoded),
                                  urlunparse)

    return f'<{next_request_url}>; rel="next"'
