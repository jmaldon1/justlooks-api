from flask import Blueprint
from os.path import dirname, basename, isfile, join
import glob

# Create a blueprint for every route in this folder
justlooks_api = Blueprint('justlooks-api', __name__)

# Import every file within this directory
modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]