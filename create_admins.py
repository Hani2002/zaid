from  werkzeug.security import generate_password_hash, check_password_hash 
import uuid 
from  configuration import admins
from functions import Operations 

obj_Operations = Operations()
for admin in admins : 
    user_obj = dict()
    user_obj['name'] = admin['name']
    user_obj['email'] = admin['email']
    user_obj['password'] = generate_password_hash(admin["password"])
    user_obj['public_id'] = str(uuid.uuid4())
    user_obj['status'] = admin["status"]
    users = obj_Operations.users 
    if user_obj['email'] not in list (users['email'] ) : 
        obj_Operations.add_row( index="users" , _object = user_obj)
obj_Operations.close_connection()
print ("Created Admins")