# create blueprint in authentication/__init__.py
from flask import Blueprint
auth = Blueprint('auth', __name__)
import  auth_views

