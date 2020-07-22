import json
import os
import ast 
import sys
import time
import boto3
import time
time.ctime() 

from datetime import datetime

# -- Variables global -- #
SOURCE_BUCKET          = os.environ['SOURCE_BUCKET']
LAYER_NAME             = os.environ['LAYER_NAME']
SB_REGION              = os.environ['SB_REGION']
FCT_NAME               = os.environ['FCT_NAME']
ACCOUNT_ID             = os.environ['ACCOUNT_ID']
FILE_NAME_REQUIRMENT   = os.environ['FILE_NAME_REQUIRMENT']
FILE_EXTENTION         = os.environ['FILE_EXTENTION']
DEPLOYER_NAME          = os.environ['DEPLOYER_NAME']
PUBLISHER_NAME         = os.environ['PUBLISHER_NAME']
TOPIC_SNS              = os.environ['TOPIC_SNS']

# -- Alias -- #
s3                     = boto3.client('s3', region_name=SB_REGION)
client                 = boto3.client('lambda', region_name=SB_REGION)
cf                     = boto3.client('cloudformation', region_name=SB_REGION)

def lambda_handler(event, context):
    
    # -- Init -- #
    DATE  = datetime.now().strftime("%d-%m-%Y_%H.%M.%S")
    warnings = None
    FILE_NAME = None
    InitLogs(SOURCE_BUCKET,DATE)
    
    """  ------ ETAPE #1 : SELECTIONNER LE FICHIER ------- """
    #Get list of object
    try :
        response = s3.list_objects(Bucket=SOURCE_BUCKET)
    except Exception as e :
        NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,SB_REGION,False,True,("Impossible to acces Bucket Source in " + SB_REGION + ", " + str(e)))
        return {'statusCode' : 200,'body' : "Lambda 'Piepline Manager' ended before finishing task : " + str(e)}
    
    #Find the one that matches requirement
    for obj in response['Contents']:
        if( obj['Key'].startswith(FILE_NAME_REQUIRMENT) and obj['Key'].endswith(FILE_EXTENTION) ):
            FILE_NAME = obj['Key']
    
    if not FILE_NAME :
        NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,SB_REGION,False,True,("No files matches the requirement (A " +FILE_EXTENTION + " that start with :" + FILE_NAME_REQUIRMENT + ") in " + SB_REGION))
        return {'statusCode' : 200,'body' : "Lambda 'Piepline Manager' ended before finishing task : " + str(e)}


    """  ------ ETAPE #2 : DEPLOYER SUR LA 1ER LAMBDA ------- """
    
    try :
        responseOfDeployment = client.invoke(
        	FunctionName = PUBLISHER_NAME,
        	Payload=json.dumps({
            	'SOURCE_BUCKET' : SOURCE_BUCKET,
            	'LAYER_NAME'    : LAYER_NAME,
            	'SB_REGION'     : SB_REGION,
            	'FCT_NAME'      : FCT_NAME,
              	'ACCOUNT_ID'    : ACCOUNT_ID,
              	'FILE_NAME'     : FILE_NAME,
              	'DATE'          : DATE,
              	'TEMP_BUCKET'   : SOURCE_BUCKET,
              	'TOPIC_SNS'     : TOPIC_SNS,
              	'REGION'        : SB_REGION
        	}),
        	InvocationType = 'RequestResponse', # Lancement des Lambdas de manière syncrone !!
        )
        print("In "+ SB_REGION +", status code " + str(responseOfDeployment["StatusCode"]))  # Le deployer c'est bien lancé si StatueCode 202. Pour savoir si ou c'est bien passé voir CloudWatch
    except Exception as e :
        NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,SB_REGION,False,True,("Impossible to lauched 'Layer publisher function' " + SB_REGION + ", " + str(e)))
        return {'statusCode' : 200,'body' : "Lambda 'Piepline Manager' ended before finishing task : " + str(e)}

    
    """  -------  ETAPE #3 : DEPLOYER SUR TT LES REGIONS -------- """
     
    region_list = ast.literal_eval(os.environ['region_list'])
    
    # Remove Source Bucket region if it's in region list
    try: 
        region_list.remove(SB_REGION)
    except ValueError as e : 
        pass
    for region in region_list :
        try :
            response = client.invoke(
            	FunctionName = DEPLOYER_NAME,
            	Payload=json.dumps({
                	'SOURCE_BUCKET' : SOURCE_BUCKET,
                	'LAYER_NAME'    : LAYER_NAME,
                	'SB_REGION'     : SB_REGION,
                	'FCT_NAME'      : FCT_NAME,
                  	'ACCOUNT_ID'    : ACCOUNT_ID,
                  	'FILE_NAME'     : FILE_NAME,
                  	'PUBLISHER_NAME': PUBLISHER_NAME,
                  	'DATE'          : DATE,
                  	'TOPIC_SNS'     : TOPIC_SNS,
                  	'REGION'        : region
            	}),
            	InvocationType = 'Event', # Lancement des Lambdas de manière asyncrone
            )
            print("Deployer lauched in "+ region +", status code " + str(response["StatusCode"]))  # Le deploer c'est bien lancé si StatueCode 202.
        except Exception as e :
            NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,SB_REGION,True,False,("An error occured when lauching deployer in region " + region + " , " + str(e))) 
    
    return {
        'statusCode'    : 200,
        'body'          : json.dumps('Deployment achieved sucessfuly')
    }




# -------------- Tools ------------------ #


# Initialise Logs in Source Bucket
def InitLogs(SOURCE_BUCKET,date) :
    
    file = open("/tmp/logs.txt", "w")
    file.write("LOGS " + date + " : \n")
    file.write("\n------------------------------------------------- \n") 
    file.close()
    
    s3   = boto3.client('s3', region_name=SB_REGION)
    response = s3.upload_file("/tmp/logs.txt", SOURCE_BUCKET, "logs/log"+date+".txt")


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