import psycopg2 as pg
from psycopg2 import sql
import json
import toolz
import datetime

from typing import Union
from flask import request, Response, jsonify, make_response
from urllib.parse import urlparse, urlsplit, urlunparse
from functools import partial
from webargs.flaskparser import use_kwargs
from webargs import fields, validate

from api.routes import justlooks_api
from api import utils, constants, create_paginated_links
from api.middleware import products


"""
TODO:
Paginate product response

HOW?
pick a method of paginating in postgres:
1. Keyset pagination
https://kb.objectrocket.com/postgresql/python-pagination-of-postgres-940

https://www.moesif.com/blog/technical/api-design/REST-API-Design-Filtering-Sorting-and-Pagination/

2. Implement the postgres pagination in the API endpoint

3. create custom page links that get sent in the header of a paginated response

"""


def generate_sql_query(last_id_gt: int, per_page: int, sort_by: str) -> str:
    sql_parts = [
        "SELECT *",
        "FROM public.products_with_variants",
        "WHERE %s > %s",
        "ORDER BY %s ASC",
        "LIMIT %s;"
    ]
    if sort_by != "int_id":
        pivot_value_sql_template = """
            SELECT
                product ->> %s as {col_alias}
            FROM
                public.products_with_variants
            WHERE
                int_id = %s
        """
        pivot_value_sql = sql.SQL(pivot_value_sql_template).format(col_alias=sql.Identifier(sort_by))
        # print(pivot_value_sql)
        if last_id_gt == -1:
            result = utils.get_one_source_sql_data(pivot_value_sql, (sort_by, 0,))
        else:
            result = utils.get_one_source_sql_data(pivot_value_sql, (sort_by, last_id_gt,))

        if not result:
            raise ValueError("NO PIVOT VALUE FOUND!")

        pivot_value = result[sort_by]
        # print(pivot_value)
        # where_filter = pivot_value
        where_clause = "WHERE product ->> %s >= %s"
        order_by_clause = "ORDER BY product ->> %s, int_id ASC"
        # order_by_clause_formatted = sql.SQL(order_by_clause_template).format(int_id=sql.Identifier("int_id"))
        sql_parts[2] = where_clause
        sql_parts[3] = order_by_clause

        query_vals = (sort_by, pivot_value, sort_by, per_page)
    else:
        order_by_clause = "ORDER BY int_id ASC"
        sql_parts[3] = order_by_clause

        query_vals = ("int_id", last_id_gt, per_page)
    
    seek_sql = "\n".join(sql_parts)
    results = utils.get_source_sql_data(seek_sql, query_vals)
    # print(list(results))
    return results


def sql__create_select_statement(sql_statements: list, column_names: str = "*") -> str:
    select = f"SELECT {column_names}"
    return sql_statements + [select]


def get_select_column_names(sort_by_col_name: str = None):
    if sort_by_col_name:
        sort_by_select_sql_template = "product ->> %s as {col_alias}"
        return sort_by_select_sql_template
        # return sql.SQL(sort_by_select_sql_template).format(col_alias=sql.Identifier(sort_by_col_name))
    
    return "*"


def sql__create_from_statement(sql_statements: list) -> str:
    return sql_statements + ["FROM public.products_with_variants"]


def sql__create_where_statement(sql_statements: list, where_conditions: str) -> str:
    where = f"WHERE {where_conditions}"
    return sql_statements + [where]


def create_where_conditions(sort_by: str = None):
    where_parts = []
    # if sort_by is None:
        # where_parts.append("%s > %s")

    if sort_by != "int_id":
        where_parts.append("product ->> %s >= %s")
    else:
        where_parts.append("int_id > %s")
    
    # ADD MORE FILTERS HERE
    
    return "\nAND ".join(where_parts)


def sql__create_order_statement(sql_statements: list, column_names: str = "int_id", order: str = "ASC") -> str:
    order_by = f"ORDER BY {column_names} {order}"
    return sql_statements + [order_by]


def get_order_by_column_names(sort_by_col_name: str = None):
    order_by_cols = []
    if sort_by_col_name != "int_id":
        order_by_cols.append("product ->> %s")
    
    order_by_cols.append("int_id")
    return ", ".join(order_by_cols)


def sql__create_limit_statement(sql_statements: list) -> str:
    return sql_statements + ["LIMIT %s"]


def create_sql(create_sql_funcs: list, sort_by: str = None) -> str:
    sql_parts = toolz.pipe([], *create_sql_funcs)
    return "\n".join(sql_parts) + ";"

def create_query_vals():
    (sort_by, pivot_value, sort_by, per_page)

    ("int_id", last_id_gt, per_page)
    pass


def get_pivot_value(last_id_gt: int, sort_by: str = None) -> Union[str, None]:
    if sort_by != "int_id":
        return None

    # select_col_names = get_select_column_names(sort_by)

    # pivot_value_sql_funcs = [
    #     sql__create_select_statement(column_names=select_col_names),
    #     sql__create_from_statement,
    #     lambda sql_statements: sql_statements + ["WHERE int_id = %s"]
    # ]
    pivot_value_sql_template = """
            SELECT
                product ->> %s as {col_alias}
            FROM
                public.products_with_variants
            WHERE
                int_id = %s
        """

    # pivot_value_sql_template = create_sql(pivot_value_sql_funcs)
    pivot_value_sql = sql.SQL(pivot_value_sql_template).format(col_alias=sql.Identifier(sort_by))

    if last_id_gt == -1:
        result = utils.get_one_source_sql_data(pivot_value_sql, (sort_by, 0,))
        return result[sort_by]
    else:
        result = utils.get_one_source_sql_data(pivot_value_sql, (sort_by, last_id_gt,))
        return result[sort_by]


def select_products(last_id_gt, per_page, sort_by: Union[str, None] = None, pivot_value: Union[str, None] = None):
    # print(sort_by)
    if sort_by != "int_id":
        if pivot_value is None:
            raise ValueError("NO PIVOT VALUE FOUND!")

        where_conditions = create_where_conditions(sort_by)
        order_by_col_names = get_order_by_column_names(sort_by)

        select_products_sql_funcs = [
            sql__create_select_statement,
            sql__create_from_statement,
            partial(sql__create_where_statement, where_conditions=where_conditions),
            partial(sql__create_order_statement, column_names=order_by_col_names),
            sql__create_limit_statement,
        ]

        select_products_sql = create_sql(select_products_sql_funcs)

        query_vals = (sort_by, pivot_value, sort_by, per_page)

        return utils.get_source_sql_data(select_products_sql, query_vals)
    else:
        where_conditions = create_where_conditions(sort_by)
        select_products_sql_funcs = [
            sql__create_select_statement,
            sql__create_from_statement,
            partial(sql__create_where_statement, where_conditions=where_conditions),
            sql__create_order_statement,
            sql__create_limit_statement,
        ]
        select_products_sql = create_sql(select_products_sql_funcs)
        # print(select_products_sql)
        query_vals = (last_id_gt, per_page)
        return utils.get_source_sql_data(select_products_sql, query_vals)


all_products_args = {
    "last_id_gt": fields.Int(required=False, missing=-1),
    "per_page": fields.Int(required=False, missing=10),
    "sort_by": fields.Str(required=False, missing="int_id"),
    "price": fields.List(fields.Str(required=False,
                                    validate=validate.Regexp(regex=r"^(gte|lte|gt|lt)\:(\d+)$|^(\d+)$",
                                                             error="Must be of format (gte|lte|lt|le):(integer) or just an integer. Eg. gte:100 or 100"))),
}


@justlooks_api.route("/all_products", methods=['GET'])
# @products.validate_query_params__all_products
@use_kwargs(all_products_args, location="query")
def all_products(last_id_gt, per_page, sort_by, price):
    print(last_id_gt, per_page, sort_by, price)
    # args = parser.parse(all_products_args, request)
    # print(args)
# def all_products(last_id_gt, per_page, sort_by):
    # # print(sort_by)
    # pivot_value = get_pivot_value(last_id_gt, sort_by)
    # results = select_products(last_id_gt, per_page, sort_by=sort_by, pivot_value=pivot_value)

    # # results = generate_sql_query(last_id_gt, per_page, sort_by)
    # # print(list(results))
    # # sql = """
    # #     SELECT * 
    # #     FROM public.products_with_variants
    # #     WHERE int_id > %s
    # #     ORDER BY int_id ASC
    # #     LIMIT %s;
    # # """

    # # results = utils.get_source_sql_data(sql, (last_id_gt, per_page))

    # jsonable_products = []
    # for product in results:
    #     updated_product = toolz.thread_first(product,
    #                                         (toolz.update_in, ['created_date'], utils.to_iso_format),
    #                                         (toolz.update_in, ['modified_date'], utils.to_iso_format),)

    #     jsonable_products.append(updated_product)

    # resp = make_response(jsonify(jsonable_products))

    # if jsonable_products:
    #     # Only create link header if there are more products to grab
    #     next_last_id_gt = jsonable_products[-1]['int_id']
    #     request_url = request.url
    #     link_header = create_infinite_scrolling_link_header(request_url,
    #                                                         per_page,
    #                                                         next_last_id_gt)
        
    #     # Add links to header
    #     resp.headers = link_header

    # return resp
    return "done"


def create_infinite_scrolling_link_header(request_url: str, per_page: int, last_id: int, rel: str = "next") -> dict:
    r1 = urlparse(request_url)
    updated_queries_template = f"per_page={per_page}&last_id_gt={last_id}"
    r2 = r1._replace(query=updated_queries_template)
    next_url = urlunparse(r2)
    link_header_template = f'<{next_url}>; rel="{rel}"'

    header = {"Link": link_header_template}
    return header



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


# @justlooks_api.route("/all_products", methods=['GET'])
# def all_products():
#     per_page_q = utils.__try_number(request.args.get("per_page"))
    
#     if per_page_q is None:
#         per_page = 10
#     else:
#         per_page = per_page_q
    
#     if not isinstance(per_page, int):
#         return {"error": "per_page must be an integer"}
#     elif per_page > 500:
#         return {"error": "per_page too large, please choose a smaller value"}
#     elif per_page <= 0:
#         return {"error": "per_page must be larger than 0"}
    
#     page_q = utils.__try_number(request.args.get("page"))

#     if page_q is None:
#         page = 1
#     else:
#         page = page_q
    
#     sql = """
#         SELECT 
#             *,
#             count(*) OVER ()  -- Window function to get total records in table
#         FROM public.products_with_variants
#         ORDER BY int_id ASC
#         OFFSET %s
#         LIMIT %s;
#     """

#     offset = (page - 1) * per_page

#     results = utils.get_source_sql_data(sql, (offset, per_page))

#     jsonable_products = []
#     total_records = 0
#     for product in results:
#         total_records = product['count']
#         updated_product = toolz.thread_first(product,
#                                             (toolz.update_in, ['created_date'], utils.to_iso_format),
#                                             (toolz.update_in, ['modified_date'], utils.to_iso_format),
#                                             (toolz.dissoc, 'count'))

#         jsonable_products.append(updated_product)

#     resp = make_response(jsonify(jsonable_products))

#     if jsonable_products:
#         request_url = request.url
#         link_header = create_paginated_links.create_header_links(request_url,
#                                                                  per_page,
#                                                                  page,
#                                                                  total_records)
#         # print(link_header)
#         link_header_with_count = {**link_header, "X-Total-Count": total_records}
#         resp.headers = link_header_with_count

#     return resp