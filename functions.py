#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 31 13:51:06 2020

@author: appspro
"""
import datetime 
from elasticsearch import Elasticsearch
import hashlib
import json
import pandas as pd
import numpy as np
from phonetic import Phonetics 
from configuration import (
        Elasticsearch_Host,
        Elasticsearch_Port,
        Elasticsearch_username,
        Elasticsearch_pass
)
import operator


class Operations () : 
    
    def __init__(self) : 
        Elasticsearch_URL = Elasticsearch_Host+':'+Elasticsearch_Port
        self.es = Elasticsearch( 
                        hosts=[Elasticsearch_URL],
                        http_auth=(Elasticsearch_username, Elasticsearch_pass),
                       )
        
        # Get Setting File
        self.settings_file = self.get_all_data_from_index("index_settings")
        self.settings_file = pd.DataFrame(self.settings_file[0])

        clenup = {
            "pre_processing":{'TRUE':True , "FALSE":False},
            "keys":{'TRUE':True , "FALSE":False},
            "weight_calculation":{'TRUE':True , "FALSE":False},
            "status":{'TRUE':True , "FALSE":False},
        }
        self.settings_file = self.settings_file.replace(clenup)
       
        self.normalize_file = pd.DataFrame( self.get_all_data_from_index("pre_processing")[0] )
        self.normalize_file = self.normalize_file.fillna("")
        #self.normalize_file.to_csv("pre_processing.csv") 

        self.obj_phonetics = Phonetics( settings_file = self.settings_file , normalize_file = self.normalize_file )

        self.users =  pd.DataFrame( self.get_all_data_from_index("users")[0] )
        self.users =self.users.replace(clenup)
        
        
    def close_connection(self):
        self.es.close()

    def add_to_log (self,headers, status,operation,public_id =None, input ='' , output = '' ):
        obj_log = dict() 
        obj_log['init_country']= headers['Init-Country']
        obj_log['channel_identifier']= headers['Channel-Identifier']
        obj_log['unique_reference']= headers['Unique-Reference']
        obj_log['time_stamp']= headers['Time-Stamp']
        obj_log['status']= status
        obj_log['operation']= operation
        obj_log['public_id']= public_id
        obj_log['input']= input
        obj_log['output']= output
        self.es.index( index='log' , body=obj_log )
        return True 

    def get_log_sammary(self) : 
        data = self.get_all_data_from_index("log")
        data = pd.DataFrame(data[0])
        if len (data) == 0 : 
            return [] , 200 
        
        data['status'].fillna(404,inplace=True)
        data['operation'].fillna('error',inplace=True)

        log_sammary = list()
        for country in data['init_country'].unique() : 
            country_data = data[data ['init_country']== country]

            for endpint in country_data['operation'].unique() : 

                endpint_country_data = country_data[country_data['operation']== endpint ]
                number_of_successful =  endpint_country_data[ endpint_country_data['status'] < 250 ]
                number_of_failed =  endpint_country_data[ endpint_country_data['status'] > 250 ]
                obj_log_sammary = dict()
                obj_log_sammary['init_country'] = country
                obj_log_sammary['Date_Time'] = datetime.datetime.now()
                obj_log_sammary['Number_Of_Successful_TRX'] = len (number_of_successful)
                obj_log_sammary['Number_Of_Failed_TRX'] = len (number_of_failed)
                obj_log_sammary['Page'] =  endpint 
                log_sammary.append(obj_log_sammary)

        return log_sammary , 200 



    def generate_query (self, index :str, fields:dict, size = None, _source =None  , _sort=None  ) -> dict :
        
        # lists
        phonetics_must_list, phonetics_must_not_list , phonetics_should_list  = list() , list() , list()
        deterministic_must_list , deterministic_must_not_list , deterministic_should_list  = list() , list()  ,list() 
        query = dict() 
        query['query']= dict()
        query['query']['bool']= { "must": [],"filter": [],"should": [],"must_not": [] }

        if _source != None : 
            query['_source'] = _source

        if size != None : 
            if size > 0 : 
                query['size'] = size

        settings = self.settings_file[self.settings_file['index'] == index]
        for key , value in fields.items() : 
            if value == '' or value == [] : 
                continue 
            key_info = settings[settings['field']== key]
            # Phonetics Fields
            if key_info.iloc[0,:]["search_type"] == "phonetics" : 
                match = {"match":dict() }
                key_dict = { "query": value,"fuzziness": "{}".format(key_info.iloc[0,:]["fuzzi_value"]), "operator": "and" }
                match['match'][key] = key_dict
                phonetics_must_list.append(match)

            # Deterministic Fields
            elif key_info.iloc[0,:]["search_type"] == "deterministic" : 
                term = {"match":dict() } 
                term ["match"][key] ={ 'query':value} 
                deterministic_must_list.append(term)

        # Phonetics  List 
        if phonetics_must_list != []: 
            query['query']['bool']['must'].append( {"bool":{"should": phonetics_must_list }} ) 
        if phonetics_should_list != [] :
            query['query']['bool']['must'].append( {"bool":{"should": phonetics_should_list }} ) 
        if phonetics_must_not_list != []:
            query['query']['bool']['must'].append( {"bool":{"must_not": phonetics_must_not_list }} ) 
        # Deterministic List
        if deterministic_must_list != []:
            query['query']['bool']['must'].append( {"bool":{"must": deterministic_must_list }} )
        if deterministic_should_list != []:
            query['query']['bool']['must'].append( {"bool":{"should": deterministic_should_list }} )
        if deterministic_must_not_list != []:
            query['query']['bool']['must'].append( {"bool":{"must_not": deterministic_must_not_list }} )
        return query


    def check_party_id_is_found (self , party_id , index , query = False ) : 
        query = dict()
        query['query'] = dict()
        query['query']['match'] = { "party_id": { "query": party_id, "operator": "and" } } 
        if query == True : 
            return query , 200
        result_search  = self.es.search( index= index , body = query )['hits']['hits']
        if result_search == [] : 
            return False
        return result_search , 200 

    def check_keys_is_found (self,index , keys ) :  
        query =  self.generate_query ( index = index  ,fields = keys )
        result_search  = result = self.es.search( index= index , body = query )['hits']['hits']

        if result_search == [] :
            return False 
        else : 
            return True 


    def get_all_data_from_index (self , index , size =10000 ):
        data,query = list(),dict()
        if index =='log' : 
            query['query'] = {"range": dict()}
            query['query']['range'] ={"time_stamp": { "gte": "now-1d/d"} }
        else : 
            query['query'] = {"match_all": {}}
        query['size'] = size
        result  = self.es.search( index= index , body = query )['hits']['hits']
        for obj in result :
            obj['_source']["Id"] =obj['_id']  
            data.append(obj['_source'])
        return data , 200 


    def generate_query_for_search (self, index ,_object :dict, parameters:dict , size = None, _source =None  , _sort=None  ) -> dict :
        # Phonetics lists
        phonetics_must_list , phonetics_must_not_list , phonetics_should_list = list() , list() , list()
        # Deterministic lists
        deterministic_must_list , deterministic_must_not_list , deterministic_should_list  = list() , list() , list()
        query = dict()

        query['query'] = { "bool": { "must": [], "should": [], "must_not": [] } }
        if _source != None : 
            query['_source'] = _source
        if size != None : 
            if size > 0 : 
                query['size'] = size
        if "party_id_not_in" in parameters.keys():
            if parameters['party_id_not_in'] !=[] : 
                terms = {
                        "terms":{ "party_id":parameters['party_id_not_in'] }
                        }
                deterministic_must_not_list.append(terms)
            del parameters['party_id_not_in']

        for key , value in parameters.items() : 
            if value !="" and value != None :
                match = {"match":dict() }
                key_dict = { "query": value , "operator": "and" }
                match['match'][key] = key_dict
                deterministic_must_list.append(match)
            else :
                 continue 
        if _object != None : 
            # Read Settings File
            settings = self.settings_file[self.settings_file['index'] == index]
            if index == "names" :

                
                for key , value in _object.items() : 

                    if value == "" or value == None or key not in ["first_name_ar","first_name_en","last_name_ar","last_name_en","full_name_en","full_name_ar"] : 
                        continue 

                    key_info = settings[settings['field']== key]
                    if key_info.iloc[0,:]["search_type"] == "phonetics" :

                        query_feedback = dict()
                        query_feedback["query"] = {"match": { "word": { "query": value ,"operator": "and" } } }
                        feedback = self.es.search(index="feedback" , body=query_feedback)

                        if feedback['hits']['hits'] == [] : 
                            match = {"match":dict() }
                            key_dict = { "query": value,"fuzziness": "AUTO", "operator": "and" }
                            match['match'][key] = key_dict

                            if key.lower() in ['full_name_ar','full_name_en'] and not (
                                                                                    _object['first_name_ar'] not in [None , "" , ''] or 
                                                                                    _object['first_name_en'] not in [None , "" ,''] or 
                                                                                    _object['last_name_en'] not in [None , "", ''] or
                                                                                    _object['last_name_ar'] not in [None , "", '']  ): 
                               
                                phonetics_should_list.append(match)
                            else: 
                                phonetics_must_list.append(match)

                        else: 
                            feedback_True = list()
                            feedback_False = list()
                            for obj_feedback in feedback['hits']['hits'] :
                                
                                if obj_feedback['_source']['similar_status'] == False :
                                    feedback_False.append(obj_feedback['_source']['similar_word'])

                                elif  obj_feedback['_source']['similar_status'] == True : 
                                    match = {"match":dict() }
                                    key_dict = { "query": obj_feedback['_source']['similar_word'],"fuzziness": "AUTO", "operator": "and" }
                                    match['match'][key] = key_dict
                                    feedback_True.append(match)

                            if feedback_False != [] : 
                                terms = {
                                    "terms":{ key :feedback_False }
                                    }
                                deterministic_must_not_list.append(terms)
                            
                            if feedback_True != [] : 
                                match = {"match":dict() }
                                key_dict = { "query": value,"fuzziness": "AUTO", "operator": "and" }
                                match['match'][key] = key_dict
                                feedback_True.append(match)
                                phonetics_must_list.append({"bool":{"should": feedback_True }})

                            else : 
                                match = {"match":dict() }
                                key_dict = { "query": value,"fuzziness": "AUTO", "operator": "and" }
                                match['match'] = key_dict
                                feedback_True.append(match)
                                phonetics_must_list.append(match)

            elif index == "nationalities" :

                if  _object != {} and _object != []  :
                    if len (_object) == 1 : 
                            for key , value in _object[0].items() : 
                                if value == "" or value == None : 
                                    continue 
                                # Deterministic Fields
                                term = {"match":dict() }  
                                term['match'][key] = { 'query':value , "operator": "and" } 
                                deterministic_must_list.append(term)
                    else: 
                        for obj in _object : 
                            for key , value in obj.items() : 
                                    if value == "" : 
                                        continue 
                                    # Deterministic Fields
                                    term = {"match":dict() }  
                                    term['match'][key] = { 'query':value , "operator": "and" } 
                                    deterministic_should_list.append(term)



        must = phonetics_must_list + deterministic_must_list 
        if   must != [] :           
            query['query']['bool']['must'].append( {"bool":{"must": must }} ) 

        should = phonetics_should_list + deterministic_should_list
        if should != []:
            query['query']['bool']['should'].append( {"bool":{"should": should }} )

        if deterministic_must_not_list != []:
            query['query']['bool']['must_not'] = deterministic_must_not_list 
        return query 


    def Search_using_party_id (self, parameters:dict ) -> list : 
            data = dict()
            for index in ['names','parties_country','nationalities']:
                query =  self.generate_query_for_search ( 
                    index =index , 
                    _object=None,
                    parameters=parameters , 
                    size=None, 
                    _source=None, 
                    _sort=None)

                result = self.es.search(index=index , body=query)
                items = dict()
                settings = self.settings_file[ (self.settings_file['index'] == index ) & ( self.settings_file['keys']== False )  ]

                if  result["hits"]["hits"] != list() and index != "nationalities" : 

                    for ind  ,  row in settings.iterrows() : 
                        if row['field'] in result["hits"]["hits"][0]['_source'].keys()  and row['field'] != "party_id"  : 
                            items[row['field']] = result["hits"]["hits"][0]['_source'][row['field']]
                    data[index] = items

                elif index == "nationalities" :
                    nal = list()
                    for obj in result["hits"]["hits"] :
                        items = dict() 
                        for ind  ,  row in settings.iterrows() : 
                            if row['field'] in obj['_source'].keys()  and row['field'] != "party_id"  : 
                                items[row['field']] = obj['_source'][row['field']]
                        nal.append(items) 
                    data[index] = nal
                else :
                    data[index] = dict()
                    continue

            if data['names'] == dict() : 
                return None 

            else :
                return data 

    def Search (self, _object:dict, parameters:dict, size=None, _source=None, _sort=None, pre_processing=True, init_country='jo', return_query=False  ) -> list : 

        source_obj = dict() 
        source_obj['keys'] = parameters.copy()
        del source_obj['keys']['party_id_not_in']

        if ( parameters['party_id'] != '' and parameters['role'] != '' and
             parameters['sequence'] != '' and parameters['source_country'] != '' and parameters['organization'] != '') : 

            _object = self.Search_using_party_id(parameters)
            if _object == None : 
                return {"status":False , 'msg':'Party ID is not found in names.'} , 404
            del parameters['party_id'] ,  parameters['role'] , parameters['sequence'] , parameters['source_country'] ,parameters['organization']
            source_obj['object'] = _object
        else :
            source_obj['object'] = _object
        
        # Names
        
        query =  self.generate_query_for_search ( index ="names" , _object=_object["names"],parameters=parameters , size=size, _source=_source, _sort=_sort)
        if return_query : 
            return query , 200

        data = list()
        result = self.es.search(index="names" , body=query)
        for obj in result["hits"]["hits"] :
            if source_obj['keys']['party_id'] != '' and source_obj['keys']['role'] != '' and source_obj['keys']['sequence'] != '' and source_obj['keys']['source_country'] != '' and source_obj['keys']['organization'] != '' : 
                if obj['_source']['party_id'].lower().strip() == source_obj['keys']['party_id'].lower().strip() : 
                    continue
            index , obj_keys , obj_data = "names" , dict() , dict()

            settings = self.settings_file[ (self.settings_file['index'] == index) & ( self.settings_file['keys']== True ) ] 
            obj_data[index] = obj['_source']
            for ind  ,  key in settings.iterrows() : 
                if key['field'] in obj_data[index].keys() : 
                    obj_keys[key['field']] = obj_data[index][key['field']]
                    del obj_data[index][key['field']]

            # Nationalities
            index , keys , _source = "nationalities"  , dict() , list()
            settings = self.settings_file[self.settings_file['index'] == index ]
            for ind  ,  row  in settings.iterrows() :
                if  row['keys'] == True : 
                    if row['field'] in obj_keys.keys()  : 
                        keys[row['field']] = obj_keys[row['field']]
                    else : 
                        _source.append(row['field'])
                else : 
                    _source.append(row['field'])
            query =  self.generate_query_for_search ( index =index , _object = None , parameters = keys,size = size, _source =_source )
            result_index  = self.es.search(index=index , body=query)


            if len (result_index["hits"]["hits"]) > 0 :
                obj_data[index] = list()
                for obj_result in result_index["hits"]["hits"] : 
                    obj_data[index].append ( obj_result['_source'] )
            else : 
                obj_data[index]= list()

            # Parties and Parties Country
            for index in  ['parties','parties_country'] : 
                settings = self.settings_file[self.settings_file['index'] == index ]
                keys , _source = dict() , list()
                for ind  ,  row  in settings.iterrows() :
                    if  row['keys'] == True : 
                        if row['field'] in obj_keys.keys()  : 
                            keys[row['field']] = obj_keys[row['field']]
                        else : 
                            _source.append(row['field'])
                    else : 
                        _source.append(row['field'])
                index_object = None 
                if index in _object.keys() :
                    index_object = dict()
                    for  field in _object[index].keys() :
                        if _object[index][field].strip() != "" : 
                            index_object[field] =  _object[index][field]

                query =  self.generate_query_for_search ( index =index , _object = index_object , parameters = keys,size = size, _source =_source )
                result_index  = self.es.search(index=index , body=query)
                if result_index["hits"]["hits"] !=[] :
                    obj_data[index] = result_index["hits"]["hits"][0]['_source']                 
                elif index_object not in [None , dict() , list() ] and result_index["hits"]["hits"] ==[] :
                    obj_data = dict()
                    break
                else:
                    obj_data[index]= dict()

            if obj_data !=dict() :
                print(  "Party ID : ",obj_keys['party_id'])
                result_with_weight = self.obj_phonetics.search_similarity_for_two_object(
                                                            obj_search = source_obj['object'] ,  
                                                            obj_result = obj_data , 
                                                            pre_processing = True )

                
               
                over_all_ratio = result_with_weight['over_all_ratio']
                auto_marge = result_with_weight['auto_marge']
                del result_with_weight['over_all_ratio']
                del result_with_weight['auto_marge']

               
                if  result_with_weight['nationalities'] in [dict() ,list() , None ] : 
                    result_with_weight['nationalities'] = list()
                    for obj in obj_data['nationalities'] :
                        obj_nat = dict() 
                        for key , value in obj.items() : 
                            obj_nat[key] = {"ratio": 0 , "value":value }
                        obj_nat['section_match_ratio'] = 0 
                        result_with_weight['nationalities'].append(obj_nat)

                obj_data = {"keys": obj_keys ,"object":result_with_weight , "over_all_ratio": over_all_ratio ,'auto_marge':auto_marge}

                if over_all_ratio != 0 :
                    data.append (obj_data)

        data.sort(key=operator.itemgetter('over_all_ratio') , reverse=True )
        data = {"source" : source_obj , "result_search" : data }
        return  data , 200
            




    def compare (self , object_one :dict , object_two : dict  ,pre_processing = True , party_type='indiviuals' ) -> dict : 

        result_with_weight = self.obj_phonetics.compare_similarity_for_two_object(
                object_one = object_one ,  
                object_two = object_two , 
                pre_processing = pre_processing ,
                party_type=party_type
                )
                             
        return result_with_weight , 200
    
    def md5_hash (self , obj) : 
        word = '''{}'''.format(obj)
        word = word.strip()
        word = word.replace(', ',',')
        word = word.replace(' ,',',')
        word = word.replace(': ',':')
        word = word.replace(' :',':')
        checksum = hashlib.md5(word.encode()).hexdigest() 
        return checksum

    def checksum(self , party_id  ) :
        
        data = dict()
        json_data  = dict()
        # Parties 
        index ="parties" 
        query = dict()
        query["query"] ={"match": {"party_id": {"query": party_id , "operator": "and" } } } 
        party_id_info = self.es.search(index=index , body=query)
        party_id_info = party_id_info["hits"]["hits"]

        if  party_id_info == [] :
            return { "msg":"Coustomer is not found."} , 400
        elif party_id_info[0]["_source"]["is_deleted"]== "y" :
            return { "msg":"Coustomer is deleted."} , 400
        else : 
            obj_checksum = self.md5_hash(party_id_info[0]["_source"])  
            data = party_id_info[0]["_source"]
            #data["parties"]= {"object": party_id_info[0]["_source"] , "checksum" : obj_checksum  }

        # Nationalities 
        index ="nationalities"
        checksums =""
        nationalities_info = self.es.search(index=index , body=query)["hits"]["hits"]
        if  nationalities_info == [] :
            data["nationalities"]= { }  
        else : 
            nationalities_list = list()
            for obj in nationalities_info : 
                del  obj["_source"]['party_id']
                nationalities_list.append({"object": obj["_source"] , "checksum" : self.md5_hash(obj["_source"])  })
                checksums = checksums + obj_checksum
            data["nationalities"]= {"objects":nationalities_list , "checksum":self.md5_hash(checksums) }

        # Parties Country
        index= "parties_country"
        party_id_info = self.es.search(index=index , body=query)
        party_id_info = party_id_info["hits"]["hits"]
        if  party_id_info == [] :
            data["parties_country"]= {}
        else : 
            parties_country_list =list()
            checksums =""
            for obj in party_id_info : 
                obj_checksum = self.md5_hash(obj["_source"])
                checksums = checksums + obj_checksum
                del obj["_source"]['party_id']
                parties_country_list.append ({"object": obj["_source"] , "checksum" : obj_checksum  }) 

            over_all_checksum = self.md5_hash(checksums) 
            data["parties_country"]= {"objects":parties_country_list , "checksum":over_all_checksum }

        # Names
        index= "names"
        checksums =""
        party_id_info = self.es.search(index=index , body=query)
        party_id_info = party_id_info["hits"]["hits"]
        if  party_id_info == [] :
            data["names"]= {}
        else : 
            names_list =list() 
            for obj in party_id_info : 
                obj_names = json.dumps(obj["_source"] ).encode("utf-8") 
                obj_checksum = hashlib.md5(obj_names).hexdigest()
                checksums = checksums + obj_checksum
                del obj["_source"]['party_id']
                names_list.append ({"object": obj["_source"] , "checksum" : obj_checksum  }) 

            over_all_checksum = self.md5_hash(checksums)   
            data["names"]= {"objects":names_list , "checksum":over_all_checksum }

        # over all checksum for all data :
        over_all_checksum = json.dumps(data ).encode("utf-8") 
        over_all_checksum = hashlib.md5(over_all_checksum).hexdigest()
        data['global_checksum'] = self.md5_hash(data) 
        return data , 200 


    def add_row (self , index : str , _object : dict ) -> str : 
        result = self.es.index( index=index , body=_object )
        res = {'status':True,'msg':'the process of adding done successfully'}
        return res , 200 

    def update_row_using_elastic_id (self , index , Id  , _object ) : 

        elastic_id = Id 
        result = self.es.update( index=index ,doc_type='_doc', id=elastic_id, body={ "doc":_object } )              
        res = {'status':True,'msg':'object is updated'}
        return (res , 200)

    def update_row (self,index : str , keys :dict  ,_object : dict ) : 

        query =  self.generate_query ( index = index  ,fields = keys )
        result_search  = result = self.es.search( index= index , body = query )['hits']['hits']

        if result_search == [] :
            self.add_row(index= index , _object= _object  )
            return ({ "status":True, 'msg':'the process of adding done successfully'} , 200)

        elastic_id =result_search[0]['_id']
        result = self.es.update( index=index ,doc_type='_doc', id=elastic_id, body={ "doc":_object } )              
        res = {"status":True,'msg':'object is updated'}
        return (res , 200) 

    
    def delete_row (self, index : str , Id : dict  ):
        
        elastic_id = Id 
        try : 
            result = self.es.delete(
                                index=index,
                                id = elastic_id  
                                )
            res = { "status":True,'msg':'the process of deleting successfully'}
            return (res , 200)
        except: 
            res = { "status":False,'msg':'Id is not found.'}
            return (res , 400)


    def Add (self,objects : dict ) : 
        
        ## Parties 
        patries_data =dict()
        index = "parties"
        patries_data['party_id'] = objects['party_id']
        patries_data['party_type']= objects['party_type']
        patries_data['is_searchable']= objects['is_searchable']
        patries_data['is_deleted']= objects['is_deleted']
        
        
        if self.check_party_id_is_found( party_id = objects['party_id'],index = index ) != False :
            res = {"status":False,"msg": "Party ID is exist" }
            return res , 400 
 
        ## Names 
        index = "names"
        fields = self.settings_file[self.settings_file['index']==index]
        if objects[index] != {}  : 
            names_data = dict()
            for index_row , row in fields.iterrows(): 

                if row['keys'] == True :
                    if row['field'] in objects.keys() : 
                        names_data[row['field']] = objects[row['field']]
                    else : 
                        res = {"status":False,"msg": "index {} : {} key is requierd.".format(index ,row['field']) }
                        return res , 400
                else :
                    if row['field'] in objects[index].keys() : 
                        names_data[row['field']] = objects[index][row['field']]
                        if names_data[row['field']] == None : 
                                names_data[row['field']] = ""
                        elif type(names_data[row['field']])==str :
                            names_data[row['field']] = names_data[row['field']].strip()
                    
        ## Nationalities
        index = "nationalities"
        fields = self.settings_file[self.settings_file['index']==index]
        list_of_nationalities = list()
        if objects[index] not in [{} ,[] , None ,"" ] and type (objects[index]) == list : 
            for obj in objects[index] : 
                nationalities_data = dict() 
                for index_row , row in fields.iterrows(): 
                    if row['keys'] == True :
                        if row['field'] in objects.keys() : 
                            nationalities_data[row['field']] = objects[row['field']]
                        else : 
                            res = {"status":False ,"msg": "index {} : {} key is requierd.".format(index ,row['field']) }
                            return res , 400
                    else :
                        if row['field'] in obj.keys() : 
                            nationalities_data[row['field']] = obj[row['field']]
                            if nationalities_data[row['field']] == None : 
                                nationalities_data[row['field']] = ""
                            elif type(nationalities_data[row['field']]) == str :
                                nationalities_data[row['field']] = nationalities_data[row['field']].strip()
                list_of_nationalities.append(nationalities_data)

        ## Parties Country
        index = "parties_country"
        fields = self.settings_file[self.settings_file['index']==index]
        if objects[index] not in [ {} ,"" , None , [] ]  : 
            parties_country_data = dict()
            for index_row , row in fields.iterrows(): 

                if row['keys'] == True :
                    if row['field'] in objects.keys() : 
                        parties_country_data[row['field']] = objects[row['field']]
                    else : 
                        res = { 'status':False, "msg": "index {} : {} key is requierd.".format(index ,row['field']) }
                        return res , 400
                else :
                    if row['field'] in objects[index].keys() : 
                        parties_country_data[row['field']] = objects[index][row['field']]
                        if parties_country_data[row['field']] == None : 
                                parties_country_data[row['field']] = ""
                        elif type(parties_country_data[row['field']])==str : 
                            parties_country_data[row['field']]= parties_country_data[row['field']].strip()

        # Add Data to DataBase
        if patries_data not in [ None , {} , [] ] :
            self.add_row(index="parties",_object = patries_data )

        if list_of_nationalities not in [None , {} , [] ] :
            for obj_nationalities in list_of_nationalities :
                self.add_row(index="nationalities",_object = obj_nationalities)

        if names_data not in [None , {} , [] ] :
            self.add_row(index="names",_object = names_data)

        if parties_country_data not in [None , {} , [] ] : 
            self.add_row(index="parties_country",_object = parties_country_data)

        res = { 'status':True , "msg": "Objects added successfully" }
        return res , 200

    def Update (self,objects) : 
        
        ## Parties 
        patries_data =dict()
        index = "parties"
        patries_data['party_id'] = objects['party_id']
        patries_data['party_type']= objects['party_type']
        patries_data['is_searchable']= objects['is_searchable']
        patries_data['is_deleted']= objects['is_deleted']       
        patries_keys = {'party_id': objects['party_id'] }

        keys=dict()
        keys['party_id'] = objects['party_id']
        keys['organization'] = objects['organization']
        keys['role'] = objects['role']
        keys['source_country'] = objects['source_country']
        keys['sequence'] = objects['sequence']

        # if self.check_party_id_is_found( party_id = objects['party_id'],index = index ) == False :
        #     self.Add(objects)
        #     res = {'status':True,  "msg": "Objects added successfully" }
        #     return res , 200 

        if not self.check_keys_is_found(index="names" , keys= keys ) :
            self.Add(objects)
            res = {'status':True,  "msg": "Objects added successfully" }
            return res , 200 

        ## Names 
        index = "names"
        fields = self.settings_file[self.settings_file['index']==index]
        names_data = dict()
        names_keys = dict()
        if objects[index] != {}  : 
            for index_row , row in fields.iterrows()  : 
                if row['keys'] == True :
                    if row['field'] in objects.keys() : 
                        names_data[row['field']] = objects[row['field']]
                        names_keys[row['field']] = objects[row['field']]
                    else : 
                        res = {'status':False, "msg": "index {} : {} key is requierd.".format(index ,row['field']) }
                        return res , 400
                else :
                    if row['field'] in objects[index].keys() : 
                        names_data[row['field']] = objects[index][row['field']]
                        if names_data[row['field']] == None : 
                            names_data[row['field']] = ""
                        elif type(names_data[row['field']])==str :
                            names_data[row['field']]= names_data[row['field']].strip()
        ## Nationalities
        index = "nationalities"
        fields = self.settings_file[self.settings_file['index']==index]
        if objects[index] != {} : 
            list_of_nationalities = list()
            for obj in objects[index] : 

                nationalities_data = dict()
                nationalities_keys = dict() 

                for index_row , row in fields.iterrows(): 

                    if row['keys'] == True :
                        if row['field'] in objects.keys() : 
                            nationalities_data[row['field']] = objects[row['field']]
                            nationalities_keys[row['field']] = objects[row['field']]
                        else : 
                            res = { 'status':False, "msg": "index {} : {} key is requierd.".format(index ,row['field']) }
                            return res , 400
                    else :
                        if row['field'] in obj.keys() : 
                            nationalities_data[row['field']] = obj[row['field']]
                            if nationalities_data[row['field']] == None : 
                                nationalities_data[row['field']] = ""
                            elif type(nationalities_data[row['field']])==str:
                                nationalities_data[row['field']] = nationalities_data[row['field']].strip() 

                list_of_nationalities.append((nationalities_keys,nationalities_data))

        ## Parties Country
        index = "parties_country"
        fields = self.settings_file[self.settings_file['index']==index]
        parties_country_data = dict()
        parties_country_keys = dict()
        if objects[index] not in [{} , "" , None ]  : 
            for index_row , row in fields.iterrows(): 
                if row['keys'] == True :
                    if row['field'] in objects.keys() : 
                        parties_country_data[row['field']] = objects[row['field']]
                        parties_country_keys [row['field']] = objects[row['field']]
                    else : 
                        res = { 'status':False, "msg": "index {} : {} key is requierd.".format(index ,row['field']) }
                        return res , 400
                else :
                    if row['field'] in objects[index].keys() : 
                        parties_country_data[row['field']] = objects[index][row['field']]

                        if parties_country_data[row['field']] == None : 
                            parties_country_data[row['field']] = ""
                        elif type(parties_country_data[row['field']])==str :
                            parties_country_data[row['field']] = parties_country_data[row['field']].strip()

        # Add Data to DataBase 
        if patries_data != dict() : 
            index = "parties"
            self.update_row(index=index,_object = patries_data , keys= patries_keys  ) 
        else : 
            res = {'status':False,"msg": "please add parties data." }
            return res , 200  

        if list_of_nationalities != list() : 
            index = "nationalities"
            for nationalities_keys , obj_nationalities in list_of_nationalities :
                #query =  self.generate_query_for_search ( index ="nationalities" , _object = None , parameters = nationalities_keys , size = 100 , _source=None )
                query =self.generate_query ( index=index , fields = nationalities_keys , size = 1500, _source =None  , _sort=None  )
                result_index  = self.es.search(index=index , body=query)
                if len (result_index["hits"]["hits"]) > 0 :
                    for obj_result in result_index["hits"]["hits"] : 
                        self.delete_row( index=index, Id = obj_result['_id']) 
                obj_nationalities.update(nationalities_keys)
                self.add_row(index=index,_object = obj_nationalities)
                #self.update_row(index="nationalities",_object = obj_nationalities , keys=nationalities_keys)

        if names_data != dict() and names_keys != dict() : 
            self.update_row(index="names",_object = names_data , keys=names_keys)

        if parties_country_data != dict() and parties_country_keys != dict() : 
            self.update_row(index="parties_country",_object = parties_country_data , keys= parties_country_keys )

        res = {'status':True,"msg": "Objects Updated successfully." }
        return res , 200 

    def Delete (self,party_id, index , phyicaly = False ):
        result_search =  self.check_party_id_is_found (party_id = party_id , index= index , query = False)
        if result_search == False: 
            return ({'status':False,'error': 'Party id is not found.'} , 404)
        elastic_id =result_search[0][0]['_id']

        if not phyicaly : 
            result = self.es.update( index=index ,doc_type='_doc', id=elastic_id, body={ "doc":{"is_deleted":"y"} } )    
            res = { 'status':True, 'msg':'object is flag deleted .'}
        else : 
            result , status = self.delete_row(index , elastic_id )
            res = { 'status':True, 'msg': result}
        return (res , 200) 