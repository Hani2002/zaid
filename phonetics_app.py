# create blueprint in authentication/__init__.py
from flask import Blueprint
phonetics = Blueprint('phonetics', __name__)
import  phonetics_views