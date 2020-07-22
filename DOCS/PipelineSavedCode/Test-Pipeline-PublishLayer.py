import logging
import json
import sys
import ast 
import urllib3

import boto3

def lambda_handler(event, context):

    # -- Variables -- #
    REGION        = event['REGION']
    SOURCE_BUCKET = event['SOURCE_BUCKET']
    FCT_NAME      = event['FCT_NAME']
    LAYER_NAME    = event['LAYER_NAME']
    TEMP_BUCKET   = event['TEMP_BUCKET']
    ACCOUNT_ID    = event['ACCOUNT_ID']
    FILE_NAME     = event['FILE_NAME']
    SB_REGION     = event['SB_REGION']
    DATE          = event['DATE']
    TOPIC_SNS     = event['TOPIC_SNS']
    warnings      = None
    
    # -- Alias -- #
    client_regional = boto3.client('lambda', region_name=REGION)
    s3r             = boto3.resource('s3', region_name=REGION)
    
    """ ---- ETAPE 1 : UPDATE OR CREATE A LAYER ---- """    

    # Updated new layer version from sources, if it doesn't exist, create it.
    try :
        response = client_regional.publish_layer_version(
            LayerName= LAYER_NAME,
            Content={
                "S3Bucket" : TEMP_BUCKET,
                "S3Key"    : FILE_NAME,
            },
        )
    except Exception as e :
       NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,REGION,False,True,"Probeme with transfering files from in " + REGION + " , " + str(e))
    
    # -- Get the last version Number
    response = client_regional.list_layer_versions(
        LayerName = LAYER_NAME,
    )
    print("Version #"+ str(response.get("LayerVersions")[0].get("Version"))+" is ready to be deploy" )
    lastest = response.get("LayerVersions")[0].get("Version");

    """ ---- ETAPE 2 : UPDATE LAMBDA TEST FUNCTION ---- """  
    
    try :
        response = client_regional.update_function_configuration(
            FunctionName  = FCT_NAME,
            Layers        = ["arn:aws:lambda:"+REGION+":"+ACCOUNT_ID+":layer:"+LAYER_NAME+":"+str(lastest)],
        )
    except client_regional.exceptions.ResourceNotFoundException as e :
       NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,REGION,False,True,"Lambda Test is missing in " + REGION + " , " + str(e))
    
    """ ---- ETAPE 3 : SET ACL ---- """  
    
    #Get the client list
    try:
        content_object = s3r.Object(SOURCE_BUCKET, 'ACL.json')
    except Exception as e :
       NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,REGION,False,True,"Probleme getting ACL.json in temp bucket in " + REGION + " , " + str(e))
    
    try :    
        file_content = content_object.get()['Body'].read().decode('utf-8')
        json_content = json.loads(file_content)
    except Exception as e :
       NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,REGION,False,True,("An error occured when converting ACL.json file in " + REGION + " , " + str(e)))
    
    #Add Acl
    for acl_client in json_content['client_list']:
        try : 
            response = client_regional.add_layer_version_permission(
                LayerName     = LAYER_NAME,
                VersionNumber = lastest,
                StatementId   = acl_client["CLIENT_NAME"],
                Action        = 'lambda:GetLayerVersion',
                Principal     = str(acl_client["CLIENT_ID"])
            )
        except client_regional.exceptions.ResourceConflictException as e :
           NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,REGION,False,True,("ACL exeptions in " + REGION + " , " + str(e)))

    
    """ ---- ETAPE 4 : INVOK THE LAMBDA  ---- """     
    
    # -- Invoke a Lambda
    try : 
        response = client_regional.invoke(
        	FunctionName   = FCT_NAME,
        	InvocationType = 'RequestResponse',
        )
    except Exception as e :
       NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,REGION,False,True,"Invok Lambda failed in " + REGION + " , " + str(e))
        
    if warnings :
       NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,REGION,True,True,lastest,warnings)
    else : 
       NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,REGION,True,True,lastest)
        
    print("Sucessfuly deploy in " + REGION)
    
    return {
        'statusCode' : 200,
        'body'       : "Sucessfuly deploy vr"+ str(lastest) +" in " + REGION
    }




# --------- TOOLS ---------- #

# Write in Logs
def NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,date,region,sucess,snsmsg,*args) :
    
    client = boto3.client('lambda', region_name=SB_REGION)
    
    responseOfDeployment = client.invoke(
        	FunctionName = "Test-Pipeline-Notification-Manager",
        	Payload=json.dumps({
            	'SOURCE_BUCKET' : SOURCE_BUCKET,
            	'SB_REGION'     : SB_REGION,
              	'ACCOUNT_ID'    : ACCOUNT_ID,
              	'DATE'          : date,
              	'TOPIC_SNS'     : TOPIC_SNS,
              	'snsmsg'        : snsmsg,
              	'REGION'        : region,
              	'SUCCESS'       : sucess,
              	'Payload'       : args
        	}),
        	InvocationType = 'RequestResponse', # Lancement des Lambdas de manière syncrone !!
    )