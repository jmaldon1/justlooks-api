import os
from typing import Any

def read_file(path: str) -> str:
    """
    Reads a file given a relative or absolute path
    """
    abs_path = os.path.abspath(path)
    with open(abs_path, encoding="utf-8-sig") as file:
        return file.read()


def is_filter_allowed(filter: str) -> bool:
    # Allowed filter values take the form of `table_column_operator`
    # `*` means all
    allowed_filters = {
        "products_*_eq"
    }


def remove_single_length_lists(val: list) -> Any:
    """
    Check if the list has a length of 1
    and if it does, return that value from the list
    """
    if len(val) == 1:
        return val[0]
    return val
