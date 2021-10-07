# create blueprint in authentication/__init__.py
from flask import Blueprint
settings_app = Blueprint('settings', __name__)
import  settings_views