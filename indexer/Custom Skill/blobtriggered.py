# Register this blueprint by adding the following line of code 
# to your entry point file.  
# app.register_functions(blobtriggered) 
# 
# Please refer to https://aka.ms/azure-functions-python-blueprints


import azure.functions as func
import logging

blobtriggered = func.Blueprint()



@blobtriggered.blob_trigger(arg_name="myblob", path="medical-xml-data",
                               connection="AzureWebJobsStorage") 
def BlobTrigger(myblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob"
                f"Name: {myblob.name}"
                f"Blob Size: {myblob.length} bytes")