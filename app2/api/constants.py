# from api import utils

def get_version():
    from api import utils
    VERSION = utils.read_file('app/VERSION')
    return VERSION
ROUTE_PATH = f"/justlooks-api/api/{VERSION}"
DB_CREDS = {
    "host": "fashion-db.cvaf5upt6dkf.us-east-2.rds.amazonaws.com",
    "dbname": "postgres",
    "user": "joshbrian"
}
ARRAY_SIZE=100
BAD_REQUEST = 400