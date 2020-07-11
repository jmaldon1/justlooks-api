import os
import psycopg2 as pg
import datetime

from typing import Union

from api import constants


def get_abs_path(path: str) -> str:
    """
    Get the absolute path of a file or folder
    """
    if not os.path.isfile(path) and not os.path.isdir(path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), os.path.abspath(path))

    return os.path.abspath(path)


def datetime_to_str(date_obj, datetime_format="%Y-%m-%dT%H-%M-%S"):
    return date_obj.strftime(datetime_format)


def str_to_datetime(date_str, datetime_format="%Y-%m-%dT%H-%M-%S"):
    return datetime.datetime.strptime(date_str, datetime_format)


def to_iso_format(datetime_o: datetime.datetime) -> str:
    return datetime_o.isoformat()


def read_file(path: str) -> str:
    """
    Reads a file given a relative or absolute path
    """
    abs_path = get_abs_path(path)
    with open(abs_path, encoding="utf-8-sig") as file:
        return file.read()


def __try_number(maybe_number):
    """The idea here is translate our INI input into something more strict,
    first try for a float, int, then concede with a string. """
    if isinstance(maybe_number, (dict, int, float, type(None))):
        return maybe_number
    else:
        try:
            fl = float(maybe_number)
            if fl.is_integer():
                return int(fl)
            else:
                return fl
        except ValueError:
            return maybe_number


def get_conn_string(secure, dbtype="msql", delim=";"):
    """get a connection string for database connection functions.
    Should probably default to pulling from environment variables or a config
    file outside of github.
    Connection string delimit their args with different things it seems; MSSQL
    via recommended pyodbc uses ; and pyodbc for postgres uses spaces. Thats
    what the delim=';' named arg is for. """
    cs = []
    for k, v in secure.items():
        assert delim not in k
        assert delim not in v
        cs.append(f"{k}={v}")

    if dbtype == "mssql" and "Pwd" not in secure:
        server = secure["server"]
        logger.info(f"Fetching password from system for host '{server}'")
        try:
            Pwd = last(netrc_fetch_password(server))
        except TypeError:
            e_msg = f"Credentials not found for '{server}' in .netrc"
            raise RuntimeError(e_msg)
        logger.info("Password retrieved")
        cs.append(f"Pwd={Pwd}")

    return delim.join(cs)


def get_source_sql_data(source_sql: str, vals: list = []):
    """with given sql cursor yield an iterator for each row. """
    arraysize = constants.ARRAY_SIZE
    conn_string = get_conn_string(constants.DB_CREDS, dbtype="postgres", delim=" ")
    with pg.connect(conn_string) as conn,\
            conn.cursor() as cur:
        cur.execute(source_sql, vals)
        # get column names; only do this once
        columns = [column[0] for column in cur.description]
        while True:
            results = cur.fetchmany(arraysize)
            if not results:
                break
            else:
                for row in results:
                    d_row = dict(zip(columns, row))
                    yield d_row


def get_one_source_sql_data(source_sql: str, vals: list = []) -> dict:
    """with given sql cursor yield an iterator for each row. """
    arraysize = constants.ARRAY_SIZE
    conn_string = get_conn_string(constants.DB_CREDS, dbtype="postgres", delim=" ")
    with pg.connect(conn_string) as conn,\
            conn.cursor() as cur:
        cur.execute(source_sql, vals)
        # get column names; only do this once
        columns = [column[0] for column in cur.description]
        result = cur.fetchone()
        if result is None:
            return {}
        return dict(zip(columns, result))


def create_error__typical(error_code: int, message: str, details: Union['str', list], details_name: str = "description") -> dict:
    return {
        "code": error_code,
        "message": message,
        details_name: details
    }


def create_error__validation(error_code: int, field: str, details: str) -> dict:
    return {
        "code": error_code,
        "field": field,
        "message": details
    }


def reformat_error_message(error_message: dict):
    print(error_message)
