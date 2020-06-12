import glob
from flask import Blueprint
from os.path import dirname, basename, isfile, join

# Create a blueprint for every route in this folder
serviceA_api = Blueprint('serviceA_api', __name__)

# Import every file within this directory
modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
