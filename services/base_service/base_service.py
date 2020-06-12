#!flask/bin/python
from flask import Flask, jsonify
from services.base_service.routes import base_service_api
from services.base_service.routes import *


def create_base_service_app(name: str):
    app = Flask(name)
    app.register_blueprint(base_service_api)
    return app


def create_base_service_app_from_config(config):
    app = create_base_service_app(config["service"]["name"])
    for key, value in config["flask"].items():
        app.config[key] = value

    return app