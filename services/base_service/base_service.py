#!flask/bin/python
from flask import Flask, jsonify, Blueprint

base_service_api = Blueprint('base_service_api', __name__)
# app = Flask(__name__)

@base_service_api.route("/health", methods=["GET"])
def health():
    state = {"status": "UP"}
    return jsonify(state)