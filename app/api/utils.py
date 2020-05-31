import os
import psycopg2 as pg
from api import constants


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


def get_source_sql_data(source_sql, vals = []):
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