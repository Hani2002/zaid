
import pandas as pd 


class validations ():

    def __init__(self , settings_file ) : 
        self.settings_file = settings_file
        self.errors = list()


    def validate__source (self,value) :

        fields = list (self.settings_file['field'].unique())

        if value == [] or value == None  :
            return None 

        if type (value) != list : 
            self.errors.append({"_source":"the data type  must a list"})
            return value

        fileds_is_not_found = list()
        for field  in  value : 
            if  field not in fields :
                fileds_is_not_found.append("{} field is not found".format(field))
        if fileds_is_not_found != [] :
            self.errors.append({"_source": fileds_is_not_found })
            return value
        return value


    def validate_pre_processing (self,value) :
        if  value in [True , False ] :
            return value
        else : 
            self.errors.append({"pre_processing":"Option '{}' is not found, please select True or False options".format(value)})
            return value

    def validate_size (self, value) :
        if type(value) != int : 
            self.errors.append({"size":"The value must be of the Integer type"})
        if value <= 0 :
            self.errors.append({"size":"size value must be greater than zero"})
        return value 

    def validate__sort (self, value) :

        if value == None : 
            return None 
        elif type(value) != bool : 
            self.errors.append({"_sort":"_sort value must boolean type"})
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