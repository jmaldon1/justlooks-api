#!flask/bin/python
import sys
import os
from flask import Flask, jsonify, make_response, Blueprint
from domain.shared.config_reader import read_config
from services.base_service.base_service import create_base_service_app_from_config
# from services.gateway.routes import gateway_api
# from services.gateway.routes import *


if __name__ == '__main__':
    host = 'localhost'
    try:
        if sys.argv[1] == 'prod':
            host = '0.0.0.0'
    except IndexError:
        pass

    if len(sys.argv) > 1:
        config_name = sys.argv[1]
    else:
        config_name = "default"

    if not config_name.endswith(".yaml"):
        config_name += ".yaml"

    config = read_config(os.path.join(os.path.dirname(__file__), "configs", config_name))

    app = create_base_service_app(config["service"]["name"])
    # app.register_blueprint(gateway_api)
    app.run(debug=True, host=host, port=config["service"]["port"])
