import psycopg2 as pg
from flask import request

from api.routes import justlooks_api
from api import utils, constants


@justlooks_api.route("/product", methods=['GET'])
def product():
    product_id = request.args.get("product_id")
    if not product_id:
        return {"Error": "'product_id' argument is required"}

    product_info = get_product(product_id)
    return product_info


def get_product(product_id: str) -> dict:
    conn_string = utils.get_conn_string(constants.DB_CREDS, dbtype="postgres", delim=" ")

    with pg.connect(conn_string) as conn, conn.cursor() as cur:
        conn.autocommit = True
        sql = """
            SELECT *
            FROM public.products_with_variants
            WHERE product_id = %s
        """

        cur.execute(sql, (product_id,))
        row = cur.fetchone()
        if row:
            return row[1]

    return {"Error": "No product found."}
