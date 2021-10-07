from flask import Flask, request, jsonify, make_response 
from flask_sqlalchemy import SQLAlchemy
from functools import wraps 
from  werkzeug.security import generate_password_hash, check_password_hash 
import uuid 
from settings_app import  settings_app 
from manage import  User , db , token_required
import jwt
from datetime import datetime
from datetime import timedelta
from functools import wraps 
from functions import Operations , validations 
from configuration import config
import json

def token_required(f): 
    @wraps(f) 
    def decorated(*args, **kwargs):
        obj_Operations = Operations() 
        token = None
        # jwt is passed in the request header 
        if 'x-access-token' in request.headers: 
            token = request.headers['x-access-token'] 
        # return 401 if token is not passed 
        if not token: 
            return jsonify({'message' : 'Token is missing !!'}), 401
   
        try: 
            # decoding the payload to fetch the stored details 
            data = jwt.decode(token, config['SECRET_KEY']) 
            users = obj_Operations.users[['email','public_id','status']]
            current_user = users.loc[users['public_id']== data['public_id'] ,:]
            current_user = list ( current_user.T.to_dict().values())[0]
            obj_Operations.close_connection()
        except: 
            return jsonify({ 
                'message' : 'Token is invalid !!'
            }), 401
        # returns the current logged in users contex to the routes 
        return  f(current_user, *args, **kwargs)
    return decorated 



@settings_app.route('/setting/', methods=['GET'])
def hello():
    return "Hello Arab Bank for Settings app"


####******************* FEEDBACK **************************####
@settings_app.route('/setting/feedback', methods=['POST'])
@token_required
def add_feedback (current_user):
    try : 
        body_keys = ["word","similar_status","similar_word","language"] 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        # Get Data
        data = request.get_json()
        headers = request.headers

        for key in body_keys : 
            if data[key] == '' : 
                return make_response({"status":False , "msg":"Please donot sned  data empty"} , 400 )


        # Validate keys : 
        for key in body_keys : 
            if key not in data.keys() :
                return {"Body":"{} key is requierd.".format(key)}

        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}

        # decoding the payload to fetch the stored details 
        if not current_user['status'] : 
            return make_response({"msg":'Only the administrator has the permission to Update.'}, 201) 

        # Add Data 
        obj_Operations = Operations()
        result , status = obj_Operations.add_row( index="feedback" , _object = data)
        obj_Operations.close_connection()
        return make_response(jsonify(result), status) 
    except : 
        results , status = { "status":False,"msg":"error in add feedback endpoint."} , 400
        return make_response(jsonify(results), status )


@settings_app.route('/setting/feedback', methods=['Get'])
@token_required
def get_feedback (current_user):
    try : 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        headers = request.headers

        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}

        if not current_user['status']: 
            return make_response({"msg":'Only the administrator has the permission to Update.'}, 201) 

        obj_Operations = Operations()
        result , status =  obj_Operations.get_all_data_from_index('feedback')
        obj_Operations.close_connection()
        return make_response(jsonify(result), status) 
    except :
        results , status = { "status":False,"msg":"error in get feedback endpoint."} , 400
        return make_response(jsonify(results), status )
    

@settings_app.route('/setting/feedback/<Id>', methods=['DELETE'])
@token_required
def delete_feedback  (current_user , Id ):
    try : 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        headers = request.headers
        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}
        
        if not current_user['status'] : 
            return make_response({"msg":'Only the administrator has the permission to Update.'}, 201) 

        obj_Operations = Operations()
        result , status =  obj_Operations.delete_row('feedback', Id)
        obj_Operations.close_connection()
    except :
        result , status = { "status":False,"msg":"error in delete feedback endpoint."} , 400
    return make_response(jsonify(result), status) 



@settings_app.route('/setting/feedback/<Id>', methods=['PUT'])
@token_required
def update_feedback  (current_user , Id ):
    try : 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        body_keys = ["word","similar_status","similar_word","language"] 
        data = request.get_json()
        headers = request.headers

        for key in body_keys : 
            if data[key] == '' : 
                return make_response({"status":False , "msg":"Please donot sned  data empty"} , 400 )

        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return  make_response({"status": False , "headers":"{} key is requierd.".format(key)} , 400 )

        for key in body_keys : 
            if key not in data.keys() : 
                return make_response({ "status":False,"Body":"{} key is requierd.".format(key)} , 400 )
        
        if not current_user['status']: 
            return make_response({"status":False ,"msg":'Only the administrator has the permission to Update.'}, 201) 

        if "Id" in data.keys() : 
            del data['Id']

        obj_Operations = Operations()
        result , status =  obj_Operations.update_row_using_elastic_id(index = 'feedback',Id =  Id, _object= data)
        obj_Operations.close_connection()
    except : 
         result , status = { "status":False,"msg":"error in delete feedback endpoint."} , 400
    return make_response(jsonify(result), status) 





### *************************** Index Settings ********************************* ### 
@settings_app.route('/setting/index_settings', methods=['Get'])
@token_required
def get_index_settings (current_user):
    try : 

        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        headers = request.headers

        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}
        
        if not current_user['status'] : 
            return make_response({"msg":'Only the administrator has the permission to Update.'}, 201) 

        obj_Operations = Operations()
        result , status =  obj_Operations.get_all_data_from_index('index_settings')
        obj_Operations.close_connection()
        
    except : 
        result , status = { "status":False,"msg":"error in get index settings endpoint."} , 400
    return make_response(jsonify(result), status) 

@settings_app.route('/setting/index_settings/', methods=['POST'])
@token_required
def add_index_settings (current_user):
    try :
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        body_keys = ["data_type","field","global_weight","index","keys","language","local_weight","pre_processing","search_type","weight_calculation"] 
        data = request.get_json()
        headers = request.headers

        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}

        for key in body_keys : 
            if key not in data.keys() : 
                return {"Body":"{} key is requierd.".format(key)}
        
        if not current_user['status']: 
            return make_response({"msg":'Only the administrator has the permission to Update.'}, 201) 

        if "Id" in data.keys() : 
            del data['Id']

        obj_Operations = Operations()
        settings_file = obj_Operations.settings_file
        new_row = settings_file[(settings_file['index']==data['index']) & (settings_file['field']==data['field'])]

        if len (new_row) == 0 : 
            result , status =  obj_Operations.add_row( index="index_settings" , _object = data)
        else : 
            result , status = { "status":False,"msg":"field : {} in table : {} already exist".format(data['field'],data['index'])} , 400
        obj_Operations.close_connection()
    except :
        result , status = { "status":False,"msg":"error in get index settings endpoint."} , 400
    return make_response(jsonify(result), status) 


@settings_app.route('/setting/index_settings/<Id>', methods=['PUT'])
@token_required
def update_index_settings (current_user , Id ):
    try : 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        body_keys = ["data_type","field","global_weight","index","keys","language","local_weight","pre_processing","search_type","weight_calculation"] 
        data = request.get_json()
        headers = request.headers

        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}

        for key in body_keys : 
            if key not in data.keys() : 
                return {"Body":"{} key is requierd.".format(key)}
        
        if not current_user['status'] : 
            return make_response({"msg":'Only the administrator has the permission to Update.'}, 201) 

        if "Id" in data.keys() : 
            del data['Id']

        obj_Operations = Operations()
        result , status =  obj_Operations.update_row_using_elastic_id(index = 'index_settings',Id =  Id, _object= data)
        obj_Operations.close_connection()
    except : 
        result , status = { "status":False,"msg":"error in update index settings endpoint."} , 400
    return make_response(jsonify(result), status) 


@settings_app.route('/setting/index_settings/<Id>', methods=['DELETE'])
@token_required
def delete_index_settings  (current_user , Id ):
    try : 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        
        headers = request.headers
        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}

        if not current_user['status'] : 
            return make_response({"msg":'Only the administrator has the permission to Update.'}, 201) 
        obj_Operations = Operations()
        result , status =  obj_Operations.delete_row('index_settings', Id)
        obj_Operations.close_connection()
    except : 
        result , status = { "status":False,"msg":"error in delete index settings endpoint."} , 400
    return make_response(jsonify(result), status) 

    ### *************************** LOG *************************** ### 


@settings_app.route('/log', methods=['GET'])
@token_required
def get_log (current_user) : 
    try : 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        headers = request.headers
        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}
        obj_Operations = Operations()
        if not current_user['status'] : 
            return make_response({"msg":'Only the administrator has the permission to Update.'}, 201) 
        result , status =  obj_Operations.get_all_data_from_index('log')
        obj_Operations.close_connection()
    except : 
        result , status = { "status":False,"msg":"error in get log  endpoint."} , 400
    return make_response(jsonify(result), status) 


@settings_app.route('/log/get_sammary', methods=['GET'])
@token_required
def get_sammary (current_user) : 
    #try : 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        headers = request.headers
        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}
        if not current_user['status'] : 
            return make_response({"msg":'Only the administrator has the permission to Update.'}, 201) 
        obj_Operations = Operations()
        result , status =  obj_Operations.get_log_sammary()
        obj_Operations.close_connection()
    #except : 
    #    result , status = { "status":False,"msg":"error in get sammary log  endpoint."} , 400
        return make_response(jsonify(result), status) 


####******************* Pre Processing **************************####
@settings_app.route('/setting/pre_processing', methods=['POST'])
@token_required
def add_pre_processing (current_user):
    try : 

        body_keys = ["language","character","replae_to"] 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        # Get Data
        data = request.get_json()
        headers = request.headers

        for key in body_keys : 
            if data[key] == '' : 
                return make_response({"status":False , "msg":"Please donot sned  data empty"} , 400 )

        # Validate keys : 
        for key in body_keys : 
            if key not in data.keys() :
                return {"Body":"{} key is requierd.".format(key)}

        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}

        if not current_user['status'] : 
            return make_response({"msg":'Only the administrator has the permission to Update.'}, 201) 

        # Add Data 
        obj_Operations = Operations()
        result , status = obj_Operations.add_row( index="pre_processing" , _object = data)
        obj_Operations.close_connection()
    except : 
        result , status = { "status":False,"msg":"error in add pre_processing endpoint."} , 400
    return make_response(jsonify(result), status) 



@settings_app.route('/setting/pre_processing', methods=['Get'])
@token_required
def get_pre_processing (current_user):
    try : 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        headers = request.headers
        endpoint = '/setting/pre_processing'
        obj_Operations = Operations()
        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}
        if not current_user['status'] :
            output = {'status':False,'msg':'Only the administrator has the permission to Update.'}
            obj_Operations.add_to_log (headers = headers , status = 400 , operation=endpoint , public_id=current_user['public_id'] , input=input , output= json.dumps(output) ) 
            obj_Operations.close_connection()
            return make_response( output , 403)
        result , status =  obj_Operations.get_all_data_from_index('pre_processing')
        obj_Operations.add_to_log (headers = headers , status = status , operation=endpoint , public_id=current_user['public_id'] , input="" , output= json.dumps(result) ) 
        obj_Operations.close_connection()
    except : 
        result , status = { "status":False,"msg":"error in get pre_processing endpoint."} , 400
    return make_response(jsonify(result), status) 


@settings_app.route('/setting/pre_processing/<Id>', methods=['DELETE'])
@token_required
def delete_pre_processing  (current_user , Id ):
    try : 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        headers = request.headers
        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}
        if not current_user['status'] : 
            return make_response({"msg":'Only the administrator has the permission to Update.'}, 201) 
        obj_Operations = Operations()
        result , status =  obj_Operations.delete_row('pre_processing', Id)
        obj_Operations.close_connection()
    except :
        result , status = { "status":False,"msg":"error in delete pre_processing endpoint."} , 400
    return make_response(jsonify(result), status) 



@settings_app.route('/setting/pre_processing/<Id>', methods=['PUT'])
@token_required
def update_pre_processing  (current_user , Id ):
    try : 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        body_keys = ["language","character","replae_to"] 
        data = request.get_json()
        headers = request.headers
        for key in body_keys : 
            if data[key] == '' : 
                return make_response({"status":False , "msg":"Please donot sned  data empty"} , 400 )
        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}
        for key in body_keys : 
            if key not in data.keys() : 
                return {"Body":"{} key is requierd.".format(key)}
    
        if not current_user['status'] : 
            return make_response({"msg":'Only the administrator has the permission to Update.'}, 201) 
        if "Id" in data.keys() : 
            del data['Id']
        obj_Operations = Operations()
        result , status =  obj_Operations.update_row_using_elastic_id(index = 'pre_processing',Id =  Id, _object= data)
        obj_Operations.close_connection()

    except : 
        result , status = { "status":False,"msg":"error in update pre_processing endpoint."} , 400
    return make_response(jsonify(result), status) 



