#!flask/bin/python
from flask import Flask, jsonify, make_response
import sys

# from app.api.constants import CSV_FOLDER, UPLOAD_FOLDER, JSON_FOLDER, ROUTE_PATH, NETRC_PATH
# from app.api import utils
# from app.api.routes import xml_parsing_api  # Import Blueprint
# from app.api.routes import *  # Import all routes
# from app.api.scheduled_tasks import delete_old_files

# cd xml-parsing-api/app
# Run script: python -m app.main
# Run: FLASK_APP=app/main.py FLASK_DEBUG=1 flask run --host=0.0.0.0 --port=5000

app = Flask(__name__)

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)
app.secret_key = 'justlooks'

# app.register_blueprint(xml_parsing_api, url_prefix=f"{app.config['ROUTE_PATH']}")


@app.errorhandler(404)
def handle_404(error):
    """
    This is returned if an undefined route is called
    """
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    host = 'localhost'
    try:
        if sys.argv[1] == 'prod':
            host = '0.0.0.0'
    except IndexError:
        pass
    app.run(debug=True, host="0.0.0.0", port=5000)
    scheduler.shutdown()
