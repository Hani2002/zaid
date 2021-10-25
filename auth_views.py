from flask import  request, jsonify, make_response 
from functools import wraps 
from  werkzeug.security import generate_password_hash, check_password_hash 
import uuid 
from auth_app import  auth 
import jwt
from datetime import datetime
from datetime import timedelta
from functions import Operations 
from configuration import config
import json


@auth.route('/auth/', methods=['GET'])
def hello():
    return "Hello Arab Bank for authentication app"  

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

@auth.route('/auth/user', methods =['GET']) 
@token_required
def get_all_users(current_user):
    try : 
        try :
            obj_Operations = Operations()
            headers = request.headers
            endpoint = '/auth/user'
            required_headers_keys = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp']
            headers = request.headers
            for key in required_headers_keys : 
                if key not in headers.keys() :
                    optput = {"headers":"{} key is requierd.".format(key)}
                    obj_Operations.add_to_log (headers = headers , status = 400 , operation=endpoint , public_id= current_user['public_id'] , output= optput) 
                    obj_Operations.close_connection()
                    return make_response(jsonify(optput) , 400) 
                    
            users = list ( obj_Operations.users[['Id','public_id','name','email']].T.to_dict().values())
        except :
            results , status = { "status":False,"msg":"error when get users data."} , 400
            return make_response(jsonify(results), status )
        try : 
            obj_Operations.add_to_log (headers = headers , status = 200 , operation=endpoint , public_id= current_user['public_id'], output = json.dumps(users) )
            obj_Operations.close_connection()
        except : 
            results , status = { "status":False,"msg":"error when add to log."} , 400
            return make_response(jsonify(results), status )
    except : 
         results , status = { "status":False,"msg":"error in auth/user endpoint."} , 400
         return make_response(jsonify(results), status ) 
    return make_response(jsonify({'users': users}) , 200) 
 

# signup route 
@auth.route('/auth/signup', methods =['POST']) 
def signup():
    try :  
        # creates a dictionary of the form data 
        data = request.get_json()
        obj_Operations = Operations()
        headers = request.headers
        endpoint = '/auth/signup'
        # Input Data for log 
        input = data.copy()
        input['password']='*************'
        input=json.dumps(input)

        # Data For create new object 
        data['status']=False
        data['email'] = data['email'].strip().lower()
        data['name'] =  data['name'].strip()
        data["password"] = generate_password_hash (data["password"])
        data["public_id"] = str(uuid.uuid4()) 

        # checking for existing user
        users = obj_Operations.users
        users = users.loc[users['email'] == data['email'] ,:]
        if users.empty:
            # Creacte object
            result , status =  obj_Operations.add_row( index="users" , _object = data)
            output = {"status":True,'msg':'Successfully registered.'}
            obj_Operations.add_to_log (headers = headers , status = status , operation=endpoint , public_id= data["public_id"] , input=input  , output=json.dumps(output)  )
            obj_Operations.close_connection()
            return make_response(output, 201) 
        else: 
            # returns 202 if user already exists 
            output = {'status':False,'msg':'User already exists. Please Login.'}
            obj_Operations.add_to_log (headers = headers , status = 202 , operation=endpoint , public_id='' , input=input , output=json.dumps(output))
            obj_Operations.close_connection()
            return make_response( output , 202) 
    except : 
       results , status = { "status":False,"msg":"error in signup endpoint."} , 400
       return make_response(jsonify(results), status )


# route for loging user in 
@auth.route('/auth/login', methods =['POST']) 
def login(): 
    #try : 
        # creates dictionary of form data 
        data = request.get_json()
        obj_Operations = Operations()
        headers = request.headers
        endpoint = "/auth/login"
        # Input Data for log 
        input = data.copy()
        input['password']='*************'
        input=json.dumps(input)
        # Check Data
        if not data or not data['email'] or not data["password"] :
            output= {'status':False,'msg':'Could not verify'}
            obj_Operations.add_to_log (headers = headers , status = 404 , operation=endpoint , public_id='' , input= input , output= json.dumps(output) )
            obj_Operations.close_connection() 
            return make_response(output, 404, {'WWW-Authenticate' : 'Basic realm ="Login required !!"'} ) 
        # Cheak user 
        users =obj_Operations.users
        users = users.loc[users['email'] == data['email'] ,:]
        if users.empty:
            # returns 404 if user does not exist 
            output = {'status':False,'msg':'Could not verify'}
            obj_Operations.add_to_log (headers = headers , status = 404 , operation=endpoint , public_id='',input=input ,output= json.dumps(output) ) 
            obj_Operations.close_connection()
            return make_response( output , 404, {'WWW-Authenticate' : 'Basic realm ="User does not exist !!"'} )
        # Check password 
        if check_password_hash(users.loc[:,'password'].values[0], data["password"] ): 
            # generates the JWT Token 
            output = "Successfully login "
            public_id= users.loc[:,'public_id'].values[0]
            token = jwt.encode({ 
                'public_id':public_id , 
                'exp' : datetime.utcnow() + timedelta(minutes = 60 * 2 ) 
            }, config['SECRET_KEY']) 
            obj_Operations.add_to_log (headers = headers , status = 201 , operation=endpoint , public_id=public_id , input=input , output=output) 
            obj_Operations.close_connection()
            return make_response(jsonify({'status':True,'token' : token.decode('UTF-8') }), 201) 
        # returns 403 if password is wrong
        output =  {'status':False,'msg':'Could not verify'}
        obj_Operations.add_to_log (headers = headers , status = 403 , operation=endpoint , public_id='' , input=input , output= json.dumps(output) )
        obj_Operations.close_connection() 
        return make_response( {'status':False,'msg':'Could not verify'}, 403, {'WWW-Authenticate' : 'Basic realm ="Wrong Password !!"'} ) 
    #except : 
    #    results , status = { "status":False,"msg":"error in login endpoint."} , 400
    #    return make_response(jsonify(results), status )

# route for loging user in 
@auth.route('/auth/change_pass', methods =['POST']) 
@token_required
def change_pass(current_user):
    try : 
        data = request.get_json()
        obj_Operations = Operations()
        headers = request.headers
        endpoint = '/auth/change_pass'
        # input data 
        input = data.copy()
        input['password']='*************'
        input=json.dumps(input)
        
        users = obj_Operations.users 
        if not current_user['status']:
            output = {'status':False,'msg':'Only the administrator has the permission to Update.'}
            obj_Operations.add_to_log (headers = headers , status = 400 , operation=endpoint , public_id=current_user['public_id'] , input=input , output= json.dumps(output) ) 
            obj_Operations.close_connection()
            return make_response( output , 403) 

        user = users.loc[users['public_id']== data['public_id'] ,:]
        if not user.empty:

            if len (data ['password'] ) < 8  :
                output = {'status':False,'msg':'Please Add Password more than 8 chracters.'}
                obj_Operations.add_to_log (headers = headers , status = 400 , operation=endpoint , public_id=current_user['public_id'] , input=input , output= json.dumps(output) ) 
                return make_response(output, 403) 
            new_object = dict()
            new_object['password'] = generate_password_hash (data ['password']) 
            new_object['email'] = user.loc[:,'email'].values[0]
            new_object['name'] = user.loc[:,'name'].values[0]
            new_object['public_id'] = user.loc[:,'public_id'].values[0]
            new_object['status'] = user.loc[:,'status'].values[0]
            result , status =  obj_Operations.update_row_using_elastic_id(index = 'users',Id =  user.loc[:,'Id'].values[0], _object= new_object)
            obj_Operations.add_to_log (headers = headers , status = status , operation=endpoint , public_id=current_user['public_id'] , input=input , output=json.dumps(result))
            obj_Operations.close_connection() 
            return make_response({'status':True,'msg':'Password Updatedd Successfully.'}, 201) 
        else :
            output = {'status':False,'msg':'Public ID is not found.'}
            obj_Operations.add_to_log (headers = headers , status = 404 , operation=endpoint , public_id=current_user['public_id'] , input=input , output=json.dumps(output)) 
            obj_Operations.close_connection()
            return make_response( output , 404) 
    except : 
        results , status = { "status":False,"msg":"error in change_pass endpoint."} , 400
        return make_response(jsonify(results), status )