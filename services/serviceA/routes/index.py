from services.serviceA.routes import serviceA_api


@serviceA_api.route("/", methods=["GET"])
def index():
    return "Hello world from service A"
