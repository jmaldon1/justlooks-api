from api.routes import justlooks_api


@justlooks_api.route("/", methods=['GET'])
def index():
    return "Hello, World!"