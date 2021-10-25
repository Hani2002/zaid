from flask import Flask, request, jsonify, make_response 
import os 
import jwt 
from functools import wraps 
from functions import Operations
from configuration import config , HOST , PORT , DEBUG
app = Flask(__name__)

# Add Configuration 
for key , value in config.items() : 
    app.config[key] = value

# Add Apps
from auth_app import auth 
from phonetics_app import phonetics
from settings_app import settings_app

app.register_blueprint(auth)
app.register_blueprint(phonetics)
app.register_blueprint(settings_app)

# Check Hello 
@app.route('/', methods=['GET'])
def hello():
    return "Hello Arab Bank"  

@app.errorhandler(400)
def handle_400_error(_error):
    """Return a http 400 error to client"""
    required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
    headers = request.headers
    obj_Operations = Operations()
    for key in required_headers_keys : 
        if key not in headers.keys() : 
            return  make_response(jsonify({'status':False ,"headers":"{} key is requierd.".format(key)}), 400)

    obj_Operations.add_to_log (headers = headers , status = 400 , operation='400_error' , public_id='')
    return make_response(jsonify({'error': 'Misunderstood'}), 400)

@app.errorhandler(401)
def handle_401_error(_error):
    """Return a http 401 error to client"""
    required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
    headers = request.headers
    obj_Operations = Operations()
    for key in required_headers_keys : 
        if key not in headers.keys() : 
            return  make_response(jsonify({'status':False ,"headers":"{} key is requierd.".format(key)}), 401)
    obj_Operations.add_to_log (headers = headers , status = 401 , operation='401_error' , public_id='')
    return make_response(jsonify({'error': 'Unauthorised'}), 401)

@app.errorhandler(404)
def handle_404_error(_error):
    """Return a http 404 error to client"""
    required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
    headers = request.headers
    obj_Operations = Operations()
    for key in required_headers_keys : 
        if key not in headers.keys() : 
            return  make_response(jsonify({'status':False ,"headers":"{} key is requierd.".format(key)}), 404)


    obj_Operations.add_to_log(headers = headers , status = 404 , operation='404_error' , public_id='')


    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(500)
def handle_500_error(_error):
    """Return a http 500 error to client"""
    return make_response(jsonify({'error': 'Server error'}), 500)

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG) 
