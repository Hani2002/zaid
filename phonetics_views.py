import json
from flask import request, jsonify, make_response 
import jwt 
from functools import wraps 
from functions import Operations 
from phonetics_app import phonetics
from configuration import config 
from validate import validations
import re

@phonetics.route('/phonetics/')
def hello():
    return 'Hello Arab Bank for phonetics app.'

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

@phonetics.route('/phonetics/checksum', methods=['GET'])
@token_required
def checksum(current_user) :
    try : 
        # Get input from request 
        data = request.get_json()

        obj_Operations = Operations() 
        # Validate Data
        obj_validations  = validations(settings_file=obj_Operations.settings_file)
        headers = obj_validations.validate_keys(error_name='headers', data = request.headers)
        data = obj_validations.validate_keys( error_name = 'primary_keys',data = data)

        ## Ceack errors
        if len (obj_validations.errors) > 0 : 
            obj_Operations.close_connection()
            return  make_response(jsonify({"errors":obj_validations.errors}), 400) 

        # Get Data form database
        try :
            results , status = obj_Operations.checksum(data)
        except :
            results , status = { "status":False,"msg":"error whean get checksum Data."} , 400

        # Add to logs
        try : 
            endpoint= "/phonetics/checksum/<party_id>"
            obj_Operations.add_to_log (headers = headers , status = status , operation=endpoint , public_id=current_user['public_id'],input=json.dumps(data) , output= json.dumps(results)) 
        except :
            results, status = { "status":False,"msg":"error whean add data to log."} , 400
    except : 
        results , status = { "status":False,"msg":"error in checksum endpoint."} , 400
    # close commection 
    obj_Operations.close_connection()
    # Return Response 
    return make_response(jsonify(results), status )
    
@phonetics.route('/phonetics/md5/', methods=['POST'])
def md5_test () :
    import json
    import hashlib
    data = request.get_json()
    word = '''{}'''.format(data)
    word = word.replace(', ',',')
    word = word.replace(' ,',',')
    word = word.replace(': ',':')
    word = word.replace(' :',':')
    checksum = hashlib.md5(word.encode()).hexdigest() 
    res = {'checksum':checksum , 'obj':word}
    return make_response(res , 200 )

@phonetics.route('/phonotics/add/', methods=['POST'])
@token_required
def Add(current_user):
    try : 
        # Get Data
        data = request.get_json()
        obj_Operations = Operations() 

        # Validate Data
        obj_validations  = validations(settings_file=obj_Operations.settings_file)
        obj_validations.validate_keys( error_name = 'json_structure',data = data , keys= ["parameters" , "object" ] )

        ## Ceack errors
        if len (obj_validations.errors) > 0 : 
            obj_Operations.close_connection()
            return  make_response(jsonify({"errors":obj_validations.errors}), 400) 

        headers = obj_validations.validate_keys(error_name='headers', data = request.headers)
        obj_validations.validate_keys( error_name = 'parameters',data = data['parameters'])
        obj_validations.validate_keys(error_name ='object' , data = data['object'] )

        ## Ceack errors
        if len (obj_validations.errors) > 0 :
            obj_Operations.close_connection() 
            return  make_response(jsonify({"errors":obj_validations.errors}), 400) 

        data['parameters'].update(data['object'])
        data = data['parameters']

        # Check if full name found or not 
        if data['names']['first_name_en'] not in [None, ""] and data['names']['last_name_en'] not in [None, ""]:#data['names']['full_name_en'] in [ "" , None ]:
            # Create Full Name english form (FN , SN , TN , LN)
            full = list()
            for  value in [data['names']['first_name_en'], data['names']['second_name_en'], data['names']['third_name_en'], data['names']['last_name_en']] : 
                if value not in [None , ""]:
                    full.append(value)
            data['names']['full_name_en'] = " ".join(full)
        if data['names']['first_name_ar'] not in [None, ""] and data['names']['last_name_ar'] not in [None, ""]:#data['names']['full_name_ar'] in ["", None ]:
            # Create Full Name arabic form (FN , SN , TN , LN)
            full = list()
            for  value in [data['names']['first_name_ar'], data['names']['second_name_ar'], data['names']['third_name_ar'], data['names']['last_name_ar']] : 
                if value not in [None , ""]:
                    full.append(value)
            data['names']['full_name_ar'] = " ".join(full)

        for key in data['names'].keys() : 
            if data['names'][key] not in [None , [] , "" ]:
                data['names'][key] = data['names'][key].strip().lower()
                data['names'][key] = re.sub(r'\s+', ' ', data['names'][key])
            
        # Add Data to database 
        try : 
            result , status = obj_Operations.Add(data)
        except : 
            result , status = {"status":False,"msg":"error when insert data in elasticsearch. "} , 400
        
        # Add to log 
        try : 
            endpoint= "/phonotics/add/"
            obj_Operations.add_to_log (headers = headers , status = status , operation=endpoint , public_id=current_user['public_id'],input=json.dumps(data),output=json.dumps(result) ) 
        except : 
            result , status = { "status":False,"msg":"error whean add data to log ."} , 400
    except : 
        result , status = { "status":False,"msg":"error in add endpoint."} , 400
    
    # close commection 
    obj_Operations.close_connection()
    # Return Response 
    return make_response(jsonify(result), status)   

@phonetics.route('/phonotics/update/<party_id>', methods=['PUT'])
@token_required
def Update(current_user , party_id):
    try :

        # Get Data
        data = request.get_json()
        obj_Operations = Operations() 

        # Validate Data
        obj_validations  = validations(settings_file=obj_Operations.settings_file)
        obj_validations.validate_keys( error_name = 'json_structure',data = data , keys= ["parameters" , "object" ] )

        ## Ceack errors
        if len (obj_validations.errors) > 0 : 
            obj_Operations.close_connection()
            return  make_response(jsonify({"errors":obj_validations.errors}), 400) 

        headers = obj_validations.validate_keys(error_name='headers', data = request.headers)
        obj_validations.validate_keys( error_name = 'parameters',data = data['parameters'] , keys=["is_searchable","is_deleted","party_type","organization","role","source_country","sequence"])
        obj_validations.validate_keys(error_name ='object' , data = data['object'] )

        ## Ceack errors
        if len (obj_validations.errors) > 0 : 
            obj_Operations.close_connection()
            return  make_response(jsonify({"errors":obj_validations.errors}), 400)

        data['parameters'].update(data['object'])
        data = data['parameters']

         # Check if full name found or not 
        if data['names']['first_name_en'] not in [None, ""] and data['names']['last_name_en'] not in [None, ""]:#data['names']['full_name_en'] in [None, ""]:
            full = list()
            for value in [data['names']['first_name_en'], data['names']['second_name_en'], data['names']['third_name_en'], data['names']['last_name_en']] :
                if value not in [None, ""]:
                    full.append(value)

            data['names']['full_name_en'] = " ".join(full)

        if data['names']['first_name_ar'] not in [None, ""] and data['names']['last_name_ar'] not in [None, ""]:#data['names']['full_name_ar'] in ["" , None ]:
            full = list()
            for  value in [data['names']['first_name_ar'], data['names']['second_name_ar'], data['names']['third_name_ar'], data['names']['last_name_ar']] : 
                if value not in [None , ""]:
                    full.append(value)

            data['names']['full_name_ar'] = " ".join(full)

        for key in data['names'].keys() : 
            if data['names'][key] not in [None , [] , "" ,{}]:
                data['names'][key] = data['names'][key].strip().lower()
                data['names'][key] = re.sub(r'\s+', ' ', data['names'][key])

        data['party_id'] = party_id

        # Update Data 
        try : 
            result , status = obj_Operations.Update(data)
        except : 
            result , status = {"status":False , "msg":"error when update data."} , 400

        # Add to log 
        try :
            endpoint= "/phonotics/update/<party_id>"
            obj_Operations.add_to_log (headers = headers , status = status , operation=endpoint , public_id=current_user['public_id'],input=json.dumps(data),output=json.dumps(result)) 
            obj_Operations.close_connection()
        except :
            result, status = { "status":False,"msg":"error whean update data to log."} , 400
    except : 
        result , status = { "status":False,"msg":"error in update endpoint."} , 400

    # close connection
    obj_Operations.close_connection()
    # return response 
    return make_response(jsonify(result), status) 

@phonetics.route('/phonotics/delete/<party_id>', methods=['DELETE'])
@token_required
def Delete(current_user , party_id):
    try : 
        obj_Operations = Operations() 
        # Validate Data
        obj_validations  = validations(settings_file=obj_Operations.settings_file)
        headers = obj_validations.validate_keys(error_name='headers', data = request.headers)
        ## Ceack errors
        if len (obj_validations.errors) > 0 : 
            obj_Operations.close_connection()
            return  make_response(jsonify({"errors":obj_validations.errors}), 400)

        # Delete object 
        try : 
            result , status = obj_Operations.Delete(index="parties" , party_id=party_id )
        except:
            result , status = { "status":False,"msg":"error in Delete object."} , 400

        # Add to log 
        try : 
            endpoint= "/phonotics/delete/<party_id>"
            obj_Operations.add_to_log (headers=headers,status=status,operation=endpoint,public_id=current_user['public_id'],input=json.dumps({'party_id':party_id}),output=json.dumps(result)) 
        except:
            result , status = { "status":False,"msg":"error whean update data to log."} , 400
    except : 
        result , status = { "status":False,"msg":"error in Delete endpoint."} , 400
    # Close Connection 
    obj_Operations.close_connection()
    # Resurn Responce 
    return make_response(jsonify(result), status )



@phonetics.route('/phonotics/search/', methods=['POST'])
@token_required
def Search(current_user):  
    try : 
        # Get Data
        data = request.get_json()
        obj_Operations = Operations() 

        # Validate Data
        obj_validations  = validations(settings_file=obj_Operations.settings_file)
        obj_validations.validate_keys( error_name = 'json_structure',data = data , keys= ["parameters" , "object" ] )

        ## Ceack errors
        if len (obj_validations.errors) > 0 : 
            obj_Operations.close_connection()
            return  make_response(jsonify({"errors":obj_validations.errors}), 400) 

        headers = obj_validations.validate_keys(error_name='headers', data = request.headers)
        obj_validations.validate_keys( error_name = 'parameters',data = data['parameters'] , 
        keys=["party_type","party_id","role","sequence","source_country","organization","party_id_not_in","pre_processing","size"])

        obj_validations.validate_keys(error_name ='object' , data = data['object'] )
        pre_processing = obj_validations.validate_pre_processing(data['parameters']['pre_processing'])
        size = obj_validations.validate_size(data['parameters']['size'])
        ## Ceack errors
        if len (obj_validations.errors) > 0 : 
            obj_Operations.close_connection()
            return  make_response(jsonify({"errors":obj_validations.errors}), 400)
        
        del data['parameters']['size']
        del data['parameters']['pre_processing']

        # Get Result
        try : 
            
            result,status = obj_Operations.Search( 
                                        _object=data['object'], 
                                        parameters=data['parameters'],
                                        size=size, 
                                        pre_processing=pre_processing, 
                                        init_country=headers['Init-Country'],
                                        return_query=False
                                        )
        except : 
            result , status = { "status":False,"msg":"error in Search object."} , 400

        # Add to log
        try :
            endpoint= "/phonotics/search/"
            obj_Operations.add_to_log (headers=headers,status=status,operation=endpoint,public_id=current_user['public_id'],input=json.dumps(data),output=json.dumps(result)) 
            obj_Operations.close_connection()
        except :
            result , status = { "status":False,"msg":"error whean update data to log."} , 400
    except:
        result , status = { "status":False,"msg":"error in Search endpoint."} , 400
    return make_response(jsonify(result),status)    


@phonetics.route('/phonotics/compare/', methods=['POST'])
@token_required
def Compare(current_user) :
    try : 
        # Get Data
        data = request.get_json()
        obj_Operations = Operations() 

        # Validate Data
        obj_validations  = validations(settings_file=obj_Operations.settings_file)
        obj_validations.validate_keys( error_name = 'json_structure',data = data , keys= ["parameters" , "object_one","object_two" ] )

        ## Ceack errors
        if len (obj_validations.errors) > 0 : 
            obj_Operations.close_connection()
            return  make_response(jsonify({"errors":obj_validations.errors}), 400) 

        headers = obj_validations.validate_keys(error_name='headers', data = request.headers)
        obj_validations.validate_keys( error_name = 'parameters',data = data['parameters'],keys=["pre_processing","party_type"])
        obj_validations.validate_keys(error_name ='object_one' , data = data['object_one'],keys=["names","nationalities","parties_country"])
        obj_validations.validate_keys(error_name ='object_two' , data = data['object_two'],keys=["names","nationalities","parties_country"])
        pre_processing = obj_validations.validate_pre_processing(data['parameters']['pre_processing'])
        ## Ceack errors
        if len (obj_validations.errors) > 0 : 
            obj_Operations.close_connection()
            return  make_response(jsonify({"errors":obj_validations.errors}), 400)

        ## Body
        party_type = data['parameters']['party_type']
        pre_processing=data['parameters']['pre_processing']
        object_one=data['object_one']
        object_two=data['object_two']

        # Get Results
        try :    
            result,status = obj_Operations.compare( party_type=party_type, pre_processing=pre_processing, object_one=object_one, object_two=object_two )
        except :
             result , status = { "status":False,"msg":"error when compare between two objects."} , 400
        
        # Add to log 
        try :
            endpoint= "/phonotics/compare/"
            obj_Operations.add_to_log (headers=headers,status=status,operation=endpoint,public_id=current_user['public_id'],input=json.dumps(data),output=json.dumps(result)) 
        except :
            result , status = { "status":False,"msg":"error whean update data to log."} , 400
    except :
        result , status = { "status":False,"msg":"error in Search endpoint."} , 400    
    # Close Connection 
    obj_Operations.close_connection()
    # Return Response 
    return make_response(jsonify(result),status)
