#!flask/bin/python
from flask import Flask, jsonify, make_response
import sys

from api.utils import reformat_error_message
from api.constants import ROUTE_PATH
# from app.api import utils
from api.routes import justlooks_api  # Import Blueprint
from api.routes import *  # Import all routes

# Run script: python app/main.py
# Run: FLASK_APP=app/main.py FLASK_DEBUG=1 flask run --host=0.0.0.0 --port=5000

app = Flask(__name__)

# app.config variables can be used anywhere that app is available
app.config['ROUTE_PATH'] = ROUTE_PATH

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)
app.secret_key = 'justlooks'

app.register_blueprint(justlooks_api, url_prefix=f"{app.config['ROUTE_PATH']}")

@app.errorhandler(404)
def handle_404(error):
    """
    This is returned if an undefined route is called
    """
    return make_response(jsonify({'error': 'Not found'}), 404)


# Return validation errors as JSON
@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    reformat_error_message(messages)
    if headers:
        return jsonify({"errors": messages}), err.code, headers
    else:
        return jsonify({"errors": messages}), err.code

# Best practices: https://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api#errors

"""How to run:
    python app/main.py  
"""
if __name__ == '__main__':
    host = 'localhost'
    try:
        if sys.argv[1] == 'prod':
            host = '0.0.0.0'
    except IndexError:
        pass
    app.run(debug=True, host=host, port=5000)
