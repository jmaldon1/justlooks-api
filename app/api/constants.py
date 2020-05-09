from api import utils

VERSION = utils.read_file('app/VERSION')
ROUTE_PATH = f"/justlooks-api/api/{VERSION}"