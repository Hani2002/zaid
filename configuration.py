import os 

# Elasticsearch
Elasticsearch_Host = '10.101.15.27'
Elasticsearch_Port= '9200'
Elasticsearch_username = 'elastic'
Elasticsearch_pass = 'abtest' 

# Flask APP 
HOST = "0.0.0.0"
PORT =8888
DEBUG = True 

config = {
    "SECRET_KEY":"#$#$Appspro_Arab_Bank$#$#",
    "SQLALCHEMY_TRACK_MODIFICATIONS":False,
    "DEBUG":True,
    "UPLOAD_FOLDER":"static/files",
    "SQLALCHEMY_DATABASE_URI": 'sqlite:///Database.bd',
    "SQLALCHEMY_COMMIT_ON_TEARDOWN":True
}

# Admins for Authinication

admins = [
    {
        "name" :'admin' , 
        "email" : "admin@Arabbank.com",
        "password":"12345" ,
        "status":True
    }
 ]

 