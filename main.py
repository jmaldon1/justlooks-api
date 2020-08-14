import os

from importlib import import_module
from flask import Flask

from app.logger import set_logger_file, logger
from app import constants
from app.api import api_bp

try:
    config_file = import_module(os.environ['JOB_CONFIG'])
    # Treat this like an import
    config = config_file.config
except KeyError as e:
    raise KeyError(f"Can't find environment variable {e}.")


# https://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api

def main():
    """Entry point of app
    Creation of flask app
    How to run:
        python main.py
    """

    set_logger_file(a_lg=logger, log_file_dir=config['module_name'])
    # Sets both File and Console level
    logger.setLevel(config['default_log_level'])
    logger.info(f"Imported from module: {os.environ['JOB_CONFIG']}")

    app = Flask(__name__)
    # app.config variables can be used anywhere that `app` is available
    app.config['ROUTE_PATH'] = constants.ROUTE_PATH
    app.config['CONFIG'] = config

    app.register_blueprint(api_bp)

    app.secret_key = 'justlooks'
    # app.run(debug=debug, host=host, port=port)
    return app


if __name__ == "__main__":
    flask_app = main()

    host = config['host']
    port = config['port']
    debug = config['debug']
    flask_app.run(debug=debug, host=host, port=port)
