import pandas as pd 


class validations ():

    def __init__(self , settings_file ) : 
        self.settings_file = settings_file
        self.errors = dict()

        # keys for validation 
        self.keys = dict()
        self.keys['headers'] = ['Init-Country','Channel-Identifier','Unique-Reference','Time-Stamp'] 
        self.keys['primary_keys'] = ["party_id","organization","role","source_country","sequence"]
        self.keys['object']=["names","nationalities","parties_country"]
        self.keys['parameters'] = ["is_searchable","is_deleted","party_id","party_type","organization","role","source_country","sequence"]

    def validate_keys (self,error_name,data ,keys = None  ) :
        if keys != None :  
            self.keys[error_name] = keys 
        # Validation for primary keys 
        errors = { error_name : list()} 
        for key in self.keys[error_name] : 
            if key not in data.keys() : 
                errors[error_name].append({"{}".format(key):"{} key is requierd.".format(key)})
        if errors[error_name] != list() :
            self.errors[error_name] = errors[error_name]
        return data



    def validate_pre_processing (self,value) :
        if  value in [True , False ] :
            return value
        else : 
            self.errors["pre_processing"] = "Option '{}' is not found, please select True or False options".format(value)
            return value

    def validate_size (self, value) :
        if type(value) != int : 
            self.errors["size"] = "The value must be of the Integer type"
        if value <= 0 :
            self.errors["size"] = "size value must be greater than zero"
        return value 


    def validate_input_object(self , index , _object ) : 
        for field , value in _object.items() :
            self.validate_field (index = index , field = field , value = value)
        return _object


    def validate_field (self, index ,field, value ) :

        field_settings = self.settings_file[(self.settings_file['index']==index)&(self.settings_file['field']==field)]

        if len (field_settings)  == 0   :
            self.errors.append({"object":"{} field is not found in index {}.".format(field , index )})
            return value

        elif len (field_settings) > 1 : 
            self.errors.append({"object":"{} field is not found in index {}.".format(field , index )})
            return value

        elif type(value).__name__ != field_settings.iloc[0,:]['data_type'].lower().strip() : 
            self.errors.append({"object":"data type {} field must {} type.".format(field , field_settings.iloc[0,:]['data_type'] )})
            return value

        return value