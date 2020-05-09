import os


def get_abs_path(path: str) -> str:
    """
    Get the absolute path of a file or folder
    """
    if not os.path.isfile(path) and not os.path.isdir(path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), os.path.abspath(path))

    return os.path.abspath(path)


def read_file(path: str) -> str:
    """
    Reads a file given a relative or absolute path
    """
    abs_path = get_abs_path(path)
    with open(abs_path, encoding="utf-8-sig") as file:
        return file.read()