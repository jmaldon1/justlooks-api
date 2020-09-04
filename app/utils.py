"""Utility functions used throughout the project
"""
import os
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse


def read_file(path: str) -> str:
    """
    Reads a file given a relative or absolute path
    """
    abs_path = os.path.abspath(path)
    with open(abs_path, encoding="utf-8-sig") as file:
        return file.read()


# def is_filter_allowed(filter: str) -> bool:
#     # Allowed filter values take the form of `table_column_operator`
#     # `*` means all
#     allowed_filters = {
#         "products_*_eq"
#     }


def replace_single_len_lists(request_params: dict) -> dict:
    """Replace any single length lists with the only item in the list

    Args:
        request_params (dict): request params

    Returns:
        dict: request params with single length lists replaced
    """
    return {key: val[0] if len(val) == 1 else val for key, val in request_params.items()}


def add_query_params_to_url(url: str, query_params: dict) -> str:
    """It takes this many lines of python to add query params to a URL for some reason.

    Args:
        url (str): URL.
        query_params (dict): Query parameters.

    Returns:
        str: URL with query parameters added.
    """
    parsed_url = urlparse(url)
    query = parsed_url.query
    url_dict = dict(parse_qsl(query))
    url_dict.update(query_params)
    url_new_query = urlencode(url_dict)
    url_parse = parsed_url._replace(query=url_new_query)
    return urlunparse(url_parse)
