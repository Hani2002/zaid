from operator import imod
import pandas as pd 
import re
from elasticsearch import Elasticsearch
from unidecode import unidecode
from difflib import SequenceMatcher
from configuration import (
        Elasticsearch_Host,
        Elasticsearch_Port,
        Elasticsearch_username,
        Elasticsearch_pass
)
from collections import Counter
from math import sqrt
#import nltk
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np 
from sklearn.metrics import jaccard_score
import string 

class Phonetics () : 
    def __init__ (self ,normalize_file  ,  settings_file ) : 
        
        self.arabic_diacritics = re.compile("""
                                 ّ    | # Tashdid
                                 َ    | # Fatha
                                 ً    | # Tanwin Fath
                                 ُ    | # Damma
                                 ٌ    | # Tanwin Damm
                                 ِ    | # Kasra
                                 ٍ    | # Tanwin Kasr
                                 ْ    | # Sukun
                                 ـ     # Tatwil/Kashida
                             """, re.VERBOSE)
                      
        
        self.settings_file = settings_file 
        self.normalize_file = normalize_file

    def remove_diacritics(self,text , language = "en"):
        text = re.sub(self.arabic_diacritics, '', text)
        return text
    
    def normalize (self,text , language = "en" ):
        normalize_file = self.normalize_file[self.normalize_file['language']==language]

        punctuation = string.punctuation 
        translator = str.maketrans('','',punctuation)
        text = text.translate(translator)

        for index , row in normalize_file.iterrows() :
            
            text = re.sub(row['character'], row['replae_to'], text)
        text = re.sub(' ','', text)
        return text.lower().strip()

    def word2vec(self,word):
        # count the characters in word
        cw = Counter(word)
        # precomputes a set of the different characters
        sw = set(cw)
        # precomputes the "length" of the word vector
        lw = sqrt(sum(c*c for c in cw.values()))
        # return a tuple
        return cw, sw, lw

    def cosdis(self,v1, v2):
        # which characters are common to the two words?
        common = v1[1].intersection(v2[1])
        # by definition of cosine distance we have
        score = sum(v1[0][ch]*v2[0][ch] for ch in common)/v1[2]/v2[2]

        if score <= 0.86 and  score > 0.60 : 
            score =score +  score * 12/100
        elif score < 0.90 and   0.85 > score  :
            score = score * 0.7/100
        if  score >= 1  : 
            score = 1

        score = score * 100 
        return  score 

    def new_score (self , word_one  , word_two ) : 

        v1 = list (''.join(format(ord(i), '08b') for i in word_one ))
        v1 =  np.array([int (i) for i in v1])
        v2 = list (''.join(format(ord(i), '08b') for i in word_two ))
        v2 = np.array([int (i) for i in v2])

        score = cosine_similarity([v1], [v2])[0][0] *100 

        if score > 78 and score < 87  : 
            score = score + 7 
        elif score <= 71 and score > 65 : 
             score = score - 5 
        return int (score) 

    # Over All Search 
    def calculate_overall_weight_for_search (self, result:dict , obj_search : dict ,  weight_type='local_weight' ) -> float :

        count ,total = 0 , 0  
        for index in  result.keys():
            settings = self.settings_file[self.settings_file['index'] == index]
            if index in ['names','parties','parties_country']:
                for key , value in result[index].items() :
                    if key in  obj_search[index].keys() : 
                        if  obj_search[index][key]  not in [ "",'' , ' ' , None ]  :
                            key_info = settings[settings['field']== key]
                            if key_info.iloc[0,:]['weight_calculation'] :
                                count += float (key_info.iloc[0,:][weight_type])
                                total = total + value['ratio']  *  float (key_info.iloc[0,:][weight_type])
                                print(key , "  " , key_info.iloc[0,:][weight_type] , "  " , value['ratio']  *  float (key_info.iloc[0,:][weight_type]) )
            else :
                
                for obj in  result[index] :
                    for key , value in obj.items() :
                        key_info = settings[settings['field']== key]
                        if  value['value']  not in [ "",'' , ' ' , None ]  :
                            if key_info.iloc[0,:]['weight_calculation'] :
                                count +=float (key_info.iloc[0,:][weight_type])
                                total = total + value['ratio']  *  float (key_info.iloc[0,:][weight_type])
                                print(key , "  " , key_info.iloc[0,:][weight_type] , "  " , value['ratio']  *  float (key_info.iloc[0,:][weight_type]) )

                if result[index] in  [list() , dict() , {} ,[] ] :
                    add_count = 0  
                    for  obj in obj_search['nationalities'] :
                        if obj ['nationality'].lower() == "jo":
                            add_count = 15
                            break
                        else : 
                            add_count = 10 
                    count = count + add_count 
        print ("total : " , total , "count : " ,count  )
        if total == 0 or count == 0 : return 0 

        total = round (total/ count ,1 )
        if total > 100 :  return 100 

        print("result :" , total )
        print ("=="*10)
    
        return total   
 
    # Over all Compare
    def calculate_overall_weight_for_compare (self, result:dict,  weight_type='local_weight' ) -> float :

        count , total = 0 , 0 
        for index in  result.keys():
            settings = self.settings_file[self.settings_file['index'] == index]
            for key , value in result[index].items() :
                if  result[index][key]['object_one'] not in ['' , ' ' , None ,""]  :
                    key_info = settings[settings['field']== key]
                    if key_info.iloc[0,:]['weight_calculation'] :
                        
                        count +=float (key_info.iloc[0,:][weight_type])
                        total = total + value['ratio']  *  float (key_info.iloc[0,:][weight_type])
                        print(key , "  " , key_info.iloc[0,:][weight_type] , "  " , value['ratio']  *  float (key_info.iloc[0,:][weight_type]) )

        if total == 0 or count == 0 : return 0 
        print ("total : " , total , "count : " ,count )

        total = round (total/ count , 1) 
        if total > 100 : 
            total = 100 

        print("result :" , total )
        return total


    def similar(self,a, b , v_doc_1 , v_doc_2 ):
        score = SequenceMatcher(None, a, b ,).ratio() 
        
        if  score <= 0.40  : 
            score = 0
        elif score <= 0.60: 
            score = score - 0.30
        

        if score < 0.15 : 
            score = 0 
        score = score * 100 
        return score 

    def similarity_ratio_calculator (self ,field_one : str, field_two : str ,language = 'ar', pre_processing=True , field_name = None ) -> float : 

        obj_field_one = field_one 
        obj_field_two = field_two
        field_one = field_one.lower().strip()
        field_two = field_two.lower().strip()
        
        
        if language == 'ar' :
            if  pre_processing == True : 
                # field one preprocssing
                field_one  = self.remove_diacritics(field_one , language = language)
                field_one = self.normalize(field_one , language = language )
                # field two preprocssing
                field_two  = self.remove_diacritics(field_two , language = language)
                field_two = self.normalize(field_two , language = language )

            if field_one == '' or field_two== '' :
                score = 0
            else :
                v_doc_1 = self.word2vec(field_one)
                v_doc_2 = self.word2vec(field_two)
                #score = self.cosdis(v_doc_1,v_doc_2)
                score = self.similar (field_one ,field_two , v_doc_1 , v_doc_2 )

        elif language == 'en' :

            if  pre_processing == True : 
                # field one preprocssing
                field_one  = self.remove_diacritics(field_one , language = language)
                field_one = self.normalize(field_one , language = language )
                # field two preprocssing
                field_two  = self.remove_diacritics(field_two , language = language)
                field_two = self.normalize(field_two , language = language )

            if field_one == '' or field_two== '' :
                score = 0
            else :
                v_doc_1 = self.word2vec(field_one)
                v_doc_2 = self.word2vec(field_two)
                #score = self.cosdis(v_doc_1,v_doc_2)
                score = self.similar (field_one ,field_two , v_doc_1 , v_doc_2 ) 

        len_v = abs (len(field_one) - len (field_two) ) 
        if len_v >= 3 and score > 88 : 
                 score = score - len_v * 6 

        if score > 99  and len (field_one) == len (field_two)  :
            score = self.new_score(field_one , field_two )

        if score >= 99 :
            score = 100 

        score = round(score, 0)
        if score > 100 :
            score = 100
        return score

    def compare_similarity_for_two_object (self , object_one : dict , object_two : dict , pre_processing = True  , party_type='indiviuals') -> dict : 
        
        obj_data = dict()
        if object_one.keys() != object_two.keys()  : 
            return {"msg":"The two objects are not identical in structure."}
            
        for index , _object in object_one.items() :
            obj_data[index] = dict() 
            if index == "nationalities" and object_one[index]!= None and  object_one[index] != []  :
                    object_one[index] = object_one[index][0]
                    object_two[index] = object_two[index][0]

            if object_one[index] in [ [] , None , "" ,{} ] or object_two[index] in [ [] , None , "" ,{} ] :
                continue 
            
            settings = self.settings_file[ (self.settings_file['index'] == index) & (self.settings_file['keys'] == False ) ]

            for  row_id , row in settings.iterrows() :
                similarity_ratio = 0 

                if row['field'] in object_one[index].keys() and row['field'] in object_two[index].keys():
                    

                    if object_one[index][row['field']] not in ["" , None , [] ] or object_two[index][row['field']] not in ["" , None , []] : 
                        if row['search_type'] == "phonetics" :

                            if  object_one[index][row['field']]  in ["" , None , [] ] : 
                                object_one[index][row['field']] =""

                            if  object_two[index][row['field']]  in ["" , None , [] ] : 
                                object_two[index][row['field']] =""

                            similarity_ratio = self.similarity_ratio_calculator(
                                                                field_one = object_one[index][row['field']] , 
                                                                field_two = object_two[index][row['field']] ,
                                                                language = row['language'] , 
                                                                pre_processing = pre_processing,
                                                                field_name= row['field']
                                                                ) 

                        elif row['search_type'] == "deterministic" : 
                            if object_one[index][row['field']]  == object_two[index][row['field']]  : 
                                similarity_ratio = 100
                            else : 
                                similarity_ratio = 0
                if row['field'] in object_one[index] and  row['field'] in object_two[index] : 
                    object_one_value = object_one[index][row['field']]
                    object_two_value = object_two[index][row['field']]
                    obj_data[index][row['field']] = {
                    "object_one":object_one_value,
                    "object_two":object_two_value,
                    "ratio":similarity_ratio
                    }
        obj_data['over_all_ratio'] = self.calculate_overall_weight_for_compare(result = obj_data )
        return obj_data




    def search_similarity_for_two_object(self , obj_search : dict , obj_result : dict , pre_processing = True  ) -> dict :
        new_obj = dict()
        
        for index in obj_search.keys () :

            if index in ['names','parties','parties_country'] :

                settings = self.settings_file[ (self.settings_file['index'] == index)]
                new_obj[index]=dict()
                for key , value in obj_result[index].items() : 
                    if key in obj_search[index].keys() :
                        field_settings =  settings[settings['field'] == key ]
                        if field_settings.iloc[0,:]['search_type'] == "phonetics":

                            if obj_search[index][key] == None : obj_search[index][key] = ""
                            if obj_result[index][key] == None : obj_result[index][key] = ""
                            field_one = obj_search[index][key].strip() 
                            field_two = obj_result[index][key].strip()
                            if field_one != '' or field_one !='' : 
                                similarity_ratio = self.similarity_ratio_calculator(
                                                                            field_one = field_one, 
                                                                            field_two = field_two,
                                                                            language =field_settings.iloc[0,:]['language'],
                                                                            pre_processing = pre_processing)  
                            else : 
                                similarity_ratio =  0
                        else : 
                            if obj_search[index][key] == obj_result[index][key] : 
                                similarity_ratio = 100 
                            else : 
                                similarity_ratio =  0
                        new_obj[index][key] = {"value":value , "ratio" : similarity_ratio  }
                    else:
                        new_obj[index][key] = {"value":value , "ratio" : 0  }

            elif index in ['nationalities'] : 

                settings = self.settings_file[ (self.settings_file['index'] == index)  ] 
                new_obj[index]=list()

                if obj_search[index] in [list() , dict() , None] :
                    for obj in obj_result[index] : 
                        obj_result_nat =dict()
                        for key , value in obj.items() : 
                            obj_result_nat[key] = {"value":value , "ratio" : 0  }
                        new_obj[index].append(obj_result_nat)
                    #new_obj = list()

                elif len ( obj_search[index]) >= 1  and len( obj_result[index])>= 1  :
                    
                    for obj in obj_result[index] :

                        for ser_obj in obj_search[index] :

                            if obj['nationality'] == ser_obj['nationality'] and ser_obj['nationality'] != "":
                                obj_result_nat =dict()
                                for key , value in obj.items() : 

                                    # similarity calculate
                                    if key in ser_obj.keys() :
                                        field_settings =  settings[settings['field'] == key ]
                                        if field_settings.iloc[0,:]['search_type'] == "phonetics": 
                                            field_one = ser_obj[key].strip() 
                                            field_two = obj[key].strip()
                                            if field_one != '' or field_one !='' : 
                                                similarity_ratio = self.similarity_ratio_calculator(
                                                                                            field_one = field_one, 
                                                                                            field_two = field_two,
                                                                                            language =field_settings.iloc[0,:]['language'],
                                                                                            pre_processing = pre_processing
                                                                                            )  
                                            else:
                                                similarity_ratio =  0
                                        else:
                                            if ser_obj[key] != "" : 
                                                if ser_obj[key] == obj[key]  : 
                                                    similarity_ratio = 100
                                                else:
                                                    similarity_ratio =  0
                                            else :
                                                similarity_ratio =  0
                                                value=""


                                        obj_result_nat[key] = {"value":value , "ratio" : similarity_ratio  }
                                    else:
                                        obj_result_nat[key] = {"value":value , "ratio" : 0  }

                                new_obj[index].append(obj_result_nat)
                                break
                            else:
                                continue
        new_obj['over_all_ratio'] = self.calculate_overall_weight_for_search(result = new_obj , obj_search = obj_search   )
        return new_obj
