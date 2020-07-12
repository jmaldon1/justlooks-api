import os

from importlib import import_module
from flask import Flask

from app.logger import set_logger_file, logger
from app import constants
from app.api import api_bp


# https://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api

def main():
    """Entry point of project
    Creation of flask app
    How to run:
        python main.py
    """
    try:
        config_file = import_module(os.environ['JOB_CONFIG'])
        secrets_file = import_module(os.environ['ENV_SECRETS'])
    except KeyError as e:
        raise KeyError(f"Can't find environment variable {e}.")

    config = config_file.config
    secrets = secrets_file.secrets

    host = config['host']
    port = config['port']
    debug = config['debug']

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
    app.run(debug=debug, host=host, port=port)


if __name__ == "__main__":
    main()
