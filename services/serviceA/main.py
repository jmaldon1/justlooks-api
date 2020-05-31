#!flask/bin/python
from flask import Flask, jsonify, make_response
import sys
from services.base_service.base_service import base_service_api

app = Flask(__name__)

app.register_blueprint(base_service_api)

@app.errorhandler(404)
def handle_404(error):
    """
    This is returned if an undefined route is called
    """
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route("/", methods=["GET"])
def index():
    return "Hello world from service A"


if __name__ == '__main__':
    host = 'localhost'
    try:
        if sys.argv[1] == 'prod':
            host = '0.0.0.0'
    except IndexError:
        pass
    app.run(debug=True, host=host, port=4000)
