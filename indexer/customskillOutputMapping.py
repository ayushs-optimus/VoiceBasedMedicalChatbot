from azure.search.documents.indexes.models import (
    OutputFieldMappingEntry
)

def OutputMapping():
    outputFieldsMapping =  [
        {
            "sourceFieldName": "/document/departments[*].patient_id",
            "targetFieldName": "patient_id"
        },
        {
            "sourceFieldName": "/document/departments[*].department_name",
            "targetFieldName": "department_name"
        },
        {
            "sourceFieldName": "/document/departments[*].department_value",
            "targetFieldName": "department_value"
        }
     ]
    return outputFieldsMapping