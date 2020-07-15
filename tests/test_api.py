import pytest
import requests
from urllib.parse import urljoin

# https://realpython.com/pytest-python-testing/


def test_basic_successful_products_call(api_endpoint: str):
    url = urljoin(api_endpoint, "products")
    query_params = {
        "int_id": "gt.0",
        "limit": 10
    }
    resp = requests.get(url, params=query_params)
    data_len = len(resp.json())
    headers = resp.headers

    assert data_len == 10
    assert resp.status_code == 200
    assert headers["Content-Range"] == "0-9/*"
    assert headers["Link"] == '<http://localhost:5000/products?int_id=gt.10&limit=10&order=int_id>; rel="next"'
    assert headers["Content-Type"] == "application/json; charset=utf-8"


@pytest.mark.parametrize("query_params, expected", [
    ({
        "int_id": "gt.0",
        "limit": 10,
    }, 10),
    ({
        "int_id": "gt.12",
        "limit": 14,
    }, 14),
    ({
        "int_id": "gt.50",
        "limit": 129,
    }, 129)
])
def test_various_limits_with_various_int_ids(api_endpoint: str, query_params: dict, expected: int):
    url = urljoin(api_endpoint, "products")
    resp = requests.get(url, params=query_params)
    data_len = len(resp.json())
    assert data_len == expected


@pytest.mark.parametrize("path", [
    "products/",
    "products/does_not_exist",
    "does_not_exist",
    "level1/level2/level3",
])
def test_404(api_endpoint: str, path: str):
    url = urljoin(api_endpoint, path)
    resp = requests.get(url)
    assert resp.status_code == 404


@pytest.mark.parametrize("query_params", [
    {},
    {
        "int_id": "gt.0",
        "limit": 10,
    },
    {
        "int_id": "gt.0",
        "limit": 10,
        "order": "base_color",
    }
])
def test_404_with_various_query_params(api_endpoint: str, query_params: dict):
    url = urljoin(api_endpoint, "does_not_exist")
    resp = requests.get(url, params=query_params)
    assert resp.status_code == 404


def test_no_data(api_endpoint: str):
    url = urljoin(api_endpoint, "products")
    query_params = {
        "int_id": "gt.999999999",
        "limit": 10,
        "order": "base_color",
    }
    resp = requests.get(url, params=query_params)
    data_len = len(resp.json())
    content_range = resp.headers['Content-Range']
    assert data_len == 0
    assert content_range == "*/*"


@pytest.mark.parametrize("query_params", [
    {
        "int_id": "gt.0",
        "limit": 2,
        "order": "base_color"
    }
])
def test_next_link_header(api_endpoint: str, query_params: dict):
    # First Request
    url = urljoin(api_endpoint, "products")
    resp = requests.get(url, params=query_params)
    data = resp.json()
    data_len = len(data)
    last_id = data[-1]["int_id"]
    assert data_len == 2

    # Next request
    link_header = resp.headers["Link"]
    link_header_parsed = requests.utils.parse_header_links(link_header)
    next_url = link_header_parsed[0]['url']
    next_resp = requests.get(next_url)
    next_data = next_resp.json()
    next_data_len = len(data)
    assert next_data_len == 2
    assert next_data[0]["int_id"] >= last_id
