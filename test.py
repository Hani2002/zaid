
{
  "query" : {
  
        "bool" : {

            "must" : [
                    {
                    "bool":{
                            "must":[
                                    { 
                                        "match": {
                                        "full_name_en": {
                                                        "query": "osama  moman",
                                                        "fuzziness": "AUTO",
                                                        "operator": "and"
                                                        }
                                        }   
                                        },

                                    { 
                                        "match": {
                                            "first_name_en": {
                                                "query": "osa",
                                                "fuzziness": "2",
                                                "operator": "and"
                                                    }
                                            }   
                                        }
                                ]
                            }

                },
        
        
        

        {
          "bool" : {
            "must" : [
              {
                "bool" : {
                  "must" : [
                    {
                      "term" : {
                        "document_type" : {
                          "value" : "id",
                          "boost" : 1.0
                        }
                      }
                    },
                    {
                      "terms" : {
                        "row_id" : [
                          1,
                          2,
                          3,
                          4,
                          5,
                          6
                        ],
                        "boost" : 1.0
                      }
                    }
                  ],
                  "adjust_pure_negative" : true,
                  "boost" : 1.0
                }
              },
              {
                "term" : {
                  "Nationality" : {
                    "value" : "jordanian",
                    "boost" : 1.0
                  }
                }
              }
            ],
            "adjust_pure_negative" : true,
            "boost" : 1.0
          }
        }
      ],
      "adjust_pure_negative" : true,
      "boost" : 1.0
    }
  }
  
}