"""Utility functions used throughout the project
"""
import os


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
