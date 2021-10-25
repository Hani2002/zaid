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

@phonetics.route('/phonetics/checksum/<party_id>', methods=['GET'])
@token_required
def checksum(current_user,party_id) :
    try : 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        headers = request.headers
        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return  make_response({"headers":"{} key is requierd.".format(key)},400)
        try :
            obj_Operations = Operations()
            results , status = obj_Operations.checksum( party_id )
        except :
            results , status = { "status":False,"msg":"error whean get checksum Data."} , 400
        try : 
            endpoint= "/phonetics/checksum/<party_id>"
            obj_Operations.add_to_log (headers = headers , status = status , operation=endpoint , public_id=current_user['public_id'],input=str(party_id) , output= json.dumps(results)) 
            obj_Operations.close_connection()
        except :
            results, status = { "status":False,"msg":"error whean add data to log."} , 400
    except : 
        results , status = { "status":False,"msg":"error in checksum endpoint."} , 400
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
    #try : 

        required_keys = ["parameters" , "object" ]
        required_parameters_keys = ["is_searchable","is_deleted","party_id","party_type","organization","role","source_country","sequence"] 
        required_object_keys = ["names","nationalities","parties_country"]
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        # Get Data
        data = request.get_json()
        headers = request.headers
        # Validate keys : 

        ### Input request 
        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}

        for key in required_keys : 
            if key not in data.keys() : 
                return {"Input":"{} key is requierd.".format(key)}

        for key in required_parameters_keys : 
            if key not in data['parameters'].keys() :
                return {"parameters":"{} key is requierd.".format(key)}

        for key in required_object_keys : 
            if key not in data['object'].keys() :
                return {"object":"{} key is requierd.".format(key)}

        data['parameters'].update(data['object'])
        data = data['parameters']

        if data['names']['full_name_en'] == "":
            full = list()
            for  value in [data['names']['first_name_en'], data['names']['second_name_en'], data['names']['third_name_en'], data['names']['last_name_en']] : 
                if value not in [None , ""]:
                    full.append(value)

            data['names']['full_name_en'] = " ".join(full)

        if data['names']['full_name_ar'] == "":
            full = list()
            for  value in [data['names']['first_name_ar'], data['names']['second_name_ar'], data['names']['third_name_ar'], data['names']['last_name_ar']] : 
                if value not in [None , ""]:
                    full.append(value)

            data['names']['full_name_ar'] = " ".join(full)

        for key in data['names'].keys() : 

            if data['names'][key] not in [None , [] , "" ]:
                data['names'][key] = data['names'][key].strip().lower()
                data['names'][key] = re.sub(r'\s+', ' ', data['names'][key])
            
        try : 
            # Add Data 
            obj_Operations = Operations()
            result , status = obj_Operations.Add(data)
        except : 
            status = 400
            result = {"status":False,"msg":"error when insert data in elasticsearch. "}

        try : 
            endpoint= "/phonotics/add/"
            obj_Operations.add_to_log (headers = headers , status = status , operation=endpoint , public_id=current_user['public_id'],input=json.dumps(data),output=json.dumps(result) ) 
            obj_Operations.close_connection()
        except : 
            results , status = { "status":False,"msg":"error whean add data to log ."} , 400
    #except : 
    #    result , status = { "status":False,"msg":"error in add endpoint."} , 400
        return make_response(jsonify(result), status) 


@phonetics.route('/phonotics/update/<party_id>', methods=['PUT'])
@token_required
def Update(current_user , party_id):
    #try :

        required_keys = ["parameters" , "object" ]
        required_parameters_keys = ["is_searchable","is_deleted","party_type","organization","role","source_country","sequence"] 
        required_object_keys = ["names","nationalities","parties_country"]
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        # Get Data
        data = request.get_json()
        headers = request.headers
        # Validate keys : 

        ### Input request 
        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}

        for key in required_keys : 
            if key not in data.keys() : 
                return {"Input":"{} key is requierd.".format(key)}

        for key in required_parameters_keys : 
            if key not in data['parameters'].keys() :
                return {"parameters":"{} key is requierd.".format(key)}

        for key in required_object_keys : 
            if key not in data['object'].keys() :
                return {"object":"{} key is requierd.".format(key)}

        data['parameters'].update(data['object'])
        data = data['parameters']

        if data['names']['full_name_en'] == "":
            full = list()
            for  value in [data['names']['first_name_en'], data['names']['second_name_en'], data['names']['third_name_en'], data['names']['last_name_en']] : 
                if value not in [None , ""]:
                    full.append(value)

            data['names']['full_name_en'] = " ".join(full)

        if data['names']['full_name_ar'] == "":
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
        #try : 
            # Update Data 
        obj_Operations = Operations()
        result , status = obj_Operations.Update(data)
        #except : 
        #    result , status = {"status":False , "msg":"error when update data."} , 400

        try :
            endpoint= "/phonotics/update/<party_id>"
            obj_Operations.add_to_log (headers = headers , status = status , operation=endpoint , public_id=current_user['public_id'],input=json.dumps(data),output=json.dumps(result)) 
            obj_Operations.close_connection()
        except :
            result, status = { "status":False,"msg":"error whean update data to log."} , 400
    #except : 
    #    result , status = { "status":False,"msg":"error in update endpoint."} , 400

        return make_response(jsonify(result), status) 

@phonetics.route('/phonotics/delete/<party_id>', methods=['DELETE'])
@token_required
def Delete(current_user , party_id):
    try : 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        # Get Data
        data = request.get_json()
        headers = request.headers
        # Validate keys : 
        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}
        try : 
            # Delete object 
            obj_Operations = Operations()
            result , status = obj_Operations.Delete(index="parties" , party_id=party_id )
        except:
            result , status = { "status":False,"msg":"error in Delete object."} , 400
        try : 
            endpoint= "/phonotics/delete/<party_id>"
            obj_Operations.add_to_log (headers=headers,status=status,operation=endpoint,public_id=current_user['public_id'],input=json.dumps(data),output=json.dumps(result)) 
            obj_Operations.close_connection()
        except:
            result , status = { "status":False,"msg":"error whean update data to log."} , 400
    except : 
        result , status = { "status":False,"msg":"error in Delete endpoint."} , 400
    return make_response(jsonify(result), status )

@phonetics.route('/phonotics/phyical_delete/<party_id>', methods=['DELETE'])
@token_required
def Phyical_Delete  (current_user , party_id ):
    try : 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        headers = request.headers
        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}
        if not current_user['status'] : 
            return make_response({"msg":'Only the administrator has the permission to Update.'}, 201) 
        obj_Operations = Operations()
        res_list = list()
        for index in ['names','parties','parties_country','nationalities']:
            result , status =  obj_Operations.Delete(index = index, party_id = party_id , phyicaly = True)
            res_list.append({"index":index , "result":result })
        obj_Operations.close_connection()
    except :
        result , status = { "status":False,"msg":"error in phyical delete endpoint."} , 400
        return make_response(jsonify(result), status) 
    return make_response(jsonify(res_list), 200) 




@phonetics.route('/phonotics/search/', methods=['POST'])
@token_required
def Search(current_user):  
    #try : 
        required_parameters_keys = [
            "party_type","party_id","role","sequence","source_country","organization","party_id_not_in","_source",
            "pre_processing","size","_sort"
        ]
        required_object_keys = ["names","nationalities","parties_country"]
        required_keys = ["parameters" , "object" ] 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        
        # Get Data and Validate Input request
        data = request.get_json()
        headers = request.headers
        
        ### Input request  
        for key in required_keys : 
            if key not in data.keys() : 
                return {"Input":"{} key is requierd.".format(key)}

        for key in required_parameters_keys : 
            if key not in data['parameters'].keys() : 
                return {"parameters":"{} key is requierd.".format(key)}

        for key in required_object_keys : 
            if key not in data['object'].keys() : 
                return {"parameters":"{} key is requierd.".format(key)}

        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}

        init_country = headers['Init-Country']
        # Validate Data
        obj_Operations = Operations() 
        
        obj_validations  = validations(settings_file=obj_Operations.settings_file)
        ### Body 
        _source =obj_validations.validate__source( data['parameters']['_source'])
        pre_processing = obj_validations.validate_pre_processing(data['parameters']['pre_processing'])
        size = obj_validations.validate_size(data['parameters']['size'])
        _sort = obj_validations.validate__sort(data['parameters']['_sort'])
        del data['parameters']['_source']
        del data['parameters']['size']
        del data['parameters']['_sort']
        del data['parameters']['pre_processing']
        # Ceack errors
        if len (obj_validations.errors) > 0 : 
            return  make_response(jsonify({"errors":obj_validations.errors}), 400) 

        if _source != None and _source !=[] : 
            for key in ["party_id","role","sequence","source_country","organization"] :
                if key not in _source : 
                    _source.append(key)
     #   try : 
        # Get Result
        
        result,status = obj_Operations.Search( 
                                    _object=data['object'], 
                                    parameters=data['parameters'],
                                    size=size, 
                                    _source=_source, 
                                    _sort=_sort, 
                                    pre_processing=pre_processing, 
                                    init_country=init_country,
                                    return_query=False
                                    )
      #  except : 
       #     result , status = { "status":False,"msg":"error in Search object."} , 400
        try :
            # Add to log 
            endpoint= "/phonotics/search/"
            obj_Operations.add_to_log (headers=headers,status=status,operation=endpoint,public_id=current_user['public_id'],input=json.dumps(data),output=json.dumps(result)) 
            obj_Operations.close_connection()
        except :
            result , status = { "status":False,"msg":"error whean update data to log."} , 400
    #except:
    #    result , status = { "status":False,"msg":"error in Search endpoint."} , 400
        return make_response(jsonify(result),status)    

@phonetics.route('/phonotics/compare/', methods=['POST'])
@token_required
def Compare(current_user) :
    #try : 
        required_parameters_keys = ["party_type","pre_processing"] 
        required_keys = ["parameters","object_one","object_two"] 
        required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
        # Get Data
        data = request.get_json()
        headers = request.headers
        # Validate keys : 
        for key in required_keys : 
            if key not in data.keys() :
                res =  {"required_keys":"{} key is requierd.".format(key)}
                return make_response(jsonify(res), 400) 

        for key in required_parameters_keys : 
            if key not in data['parameters'].keys() : 
                res =  {"parameters":"{} key is requierd.".format(key)}
                return make_response(jsonify(res), 400) 

        for key in required_headers_keys : 
            if key not in headers.keys() : 
                return {"headers":"{} key is requierd.".format(key)}

        ## Body
        party_type = data['parameters']['party_type']
        pre_processing=data['parameters']['pre_processing']
        object_one=data['object_one']
        object_two=data['object_two']
        #try :
            # Get Results
        obj_Operations = Operations()
        result,status = obj_Operations.compare( party_type=party_type, pre_processing=pre_processing, object_one=object_one, object_two=object_two )
        #except :
        #     result , status = { "status":False,"msg":"error when compare between two objects."} , 400
        try :
            # Add to log 
            endpoint= "/phonotics/compare/"
            obj_Operations.add_to_log (headers=headers,status=status,operation=endpoint,public_id=current_user['public_id'],input=json.dumps(data),output=json.dumps(result)) 
            print("==="*20)
            obj_Operations.close_connection()
        except :
            result , status = { "status":False,"msg":"error whean update data to log."} , 400
    #except :
    #    result , status = { "status":False,"msg":"error in Search endpoint."} , 400
        return make_response(jsonify(result),status)
