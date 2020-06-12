from services.base_service.routes import base_service_api
from flask import jsonify

@base_service_api.route("/health", methods=['GET'])
def health():
    state = {"status": "UP"}
    return jsonify(state)