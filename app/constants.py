from app import utils

VERSION = utils.read_file('./VERSION')
ROUTE_PATH = f"/justlooks-api/api/{VERSION}"
BAD_REQUEST = 400
