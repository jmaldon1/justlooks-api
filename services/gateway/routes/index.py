import requests
from services.gateway.routes import gateway_api


@gateway_api.route("/", methods=["GET"])
def index():
    return "Hello world"


@gateway_api.route("/serviceA", methods=["GET"])
def svcA():
    r = requests.get("http://localhost:20000/")
    return r.text
