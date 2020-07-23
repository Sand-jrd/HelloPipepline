import logging
import json
import sys
import random
import ast 
import urllib3

import boto3

def lambda_handler(event, context):
    
    # -- Variables -- #
    REGION         = event['REGION']
    SOURCE_BUCKET  = event['SOURCE_BUCKET']
    FCT_NAME       = event['FCT_NAME']
    LAYER_NAME     = event['LAYER_NAME']
    TEMP_BUCKET    = SOURCE_BUCKET+"-"+REGION+"-"+"temporary"
    ACCOUNT_ID     = event['ACCOUNT_ID']
    FILE_NAME      = event['FILE_NAME']
    SB_REGION      = event['SB_REGION']
    DATE           = event['DATE']
    TOPIC_SNS      = event['TOPIC_SNS']
    PUBLISHER_NAME = event['PUBLISHER_NAME']

    warnings       = None

    
    # -- Alias -- #
    s3              = boto3.client('s3', region_name=SB_REGION)
    client          = boto3.client('lambda', region_name=SB_REGION)
    cf              = boto3.client('cloudformation', region_name=SB_REGION)
    client_regional = boto3.client('lambda', region_name=REGION)
    s3r             = boto3.resource('s3', region_name=REGION)
    
    """ ---- ETAPE 1 : COPY LAYER FILE IN TRANSFER BUCKET ---- """
   
   #Creat a bucket
    try :
        response = s3.create_bucket(
            Bucket                    = TEMP_BUCKET,
            CreateBucketConfiguration = {'LocationConstraint': REGION }
        )
    except s3.exceptions.BucketAlreadyExists as e:
        TEMP_BUCKET = create_bucket_name_check(TEMP_BUCKET,REGION)
    except s3.exceptions.BucketAlreadyOwnedByYou as e:
        warnings = TEMP_BUCKET + " BucketAlreadyOwnedByYou, it will be reused \n"
    except Exception as e :
        NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,REGION,False,True,"Impossible to create transfer bucket in " + REGION + " , " + str(e))
        return {'statusCode' : 200,'body' : "Lambda 'Deployer' ended before finishing task : " + str(e)}
    
    #Copy all files
    try : 
        for key in s3.list_objects(Bucket=SOURCE_BUCKET)['Contents']:
            files       = key['Key']
            copy_source = {'Bucket': SOURCE_BUCKET,'Key': files}
            s3.copy(copy_source, TEMP_BUCKET, files)
    except Exception as e :
        NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,REGION,False,True,"Probeme with transfering files from " + SOURCE_BUCKET + "to " + TEMP_BUCKET + " in " + REGION + str(e))
        return {'statusCode' : 200,'body' : "Lambda 'Deployer' ended before finishing task : " + str(e)}
    
    """ ---- ETAPE 2 : Check if the lambda funcion needs to be create or not ---- """  
    
    try :
        response = client_regional.get_function(FunctionName  = FCT_NAME)
    except client_regional.exceptions.ResourceNotFoundException as e:
        create_function_from_another(FCT_NAME,REGION,TEMP_BUCKET, SB_REGION)

    """ ---- ETAPE 3 : Publish Layer ---- """ 
    print(TEMP_BUCKET)
    try :
        responseOfDeployment = client.invoke(
        	FunctionName = PUBLISHER_NAME,
        	Payload=json.dumps({
            	'SOURCE_BUCKET' : SOURCE_BUCKET,
            	'LAYER_NAME'    : LAYER_NAME,
            	'SB_REGION'     : SB_REGION,
            	'FCT_NAME'      : FCT_NAME,
              	'ACCOUNT_ID'    : ACCOUNT_ID,
              	'TEMP_BUCKET'   : TEMP_BUCKET,
              	'FILE_NAME'     : FILE_NAME,
              	'DATE'          : DATE,
              	'TOPIC_SNS'     : TOPIC_SNS,
              	'REGION'        : REGION
        	}),
                    	InvocationType = 'RequestResponse', # Lancement des Lambdas de manière syncrone !!
        )
        print("In "+ REGION +", status code " + str(responseOfDeployment["StatusCode"]))  # Le deploer c'est bien lancé si StatueCode 202. Pour savoir si ou c'est bien passé voir CloudWatch
    except Exception as e :
        NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,REGION,False,True,"Impossible to launch 'Publish Layer Function' in " + REGION +" , \n"+ str(e))
        return {'statusCode' : 200,'body' : "Lambda 'Deployer' ended before finishing task : " + str(e)}
    
    """ ---- POST : Nettoyer ---- """ 
    try :
        response = delete_bucket_completely(TEMP_BUCKET, REGION)
    except Exception as e :
        NotificationManager(SOURCE_BUCKET,SB_REGION,ACCOUNT_ID,TOPIC_SNS,DATE,REGION,True,False,"Impossible to delete temporary bucket in " + REGION + " , \n" + str(e))
     
     
    return {
        'statusCode' : 200,
        'body'       : "WorkDone"
    }

# ----------------------- FONCTION TOOLS ------------------------- #

# DELETE AN ENTIRE BUCKET
def delete_bucket_completely(bucket_name,region):
    
    # -- Alias -- #
    s3 = boto3.client('s3', region_name=region)
    client = boto3.client('lambda', region_name=region)
    
    response = s3.list_objects_v2(
        Bucket=bucket_name,
    )

    while response['KeyCount'] > 0:
        response = s3.delete_objects(
            Bucket=bucket_name,
            Delete={
                'Objects':[{'Key':obj['Key']} for obj in response['Contents']]
            }
        )
        response = s3.list_objects_v2(
            Bucket=bucket_name,
        )

    response = s3.delete_bucket(
        Bucket=bucket_name
    )

# CREATE A FUNCTION FROM AN OTHER
def create_function_from_another(function_name,region,new_bucket,sb_region):
    
    # -- Alias -- #
    s3              = boto3.client('s3', region_name=sb_region)
    client          = boto3.client('lambda', region_name=sb_region)
    http            = urllib3.PoolManager()
    client_regional = boto3.client('lambda', region_name=region)
    
    #Get config
    fct_output   = client.get_function(FunctionName=function_name)
    
    request_zip  = http.request('GET', fct_output['Code']['Location'])
    fct_data     = fct_output['Configuration']
    
    #Create function
    response = client_regional.create_function(
        FunctionName     = fct_data['FunctionName'],
        Runtime          = fct_data['Runtime'],
        Role             = fct_data['Role'],
        Handler          = fct_data['Handler'],
        Code={
            'ZipFile': request_zip.data
        },
        Description       = fct_data['Description'],
        Timeout           = fct_data['Timeout'],
        MemorySize        = fct_data['MemorySize'],
        )
    
    #Check parameters that potentialy doesn't exist
    str_config_list = ["DeadLetterConfig","Environment","TracingConfig","Tags"]
    if ("DeadLetterConfig" in fct_data.keys()) :
        client_regional.update_function_configuration(FunctionName=function_name, DeadLetterConfig = fct_data["DeadLetterConfig"])
    if ("Environment" in fct_data.keys()) :
        client_regional.update_function_configuration(FunctionName=function_name, Environment = fct_data["Environment"])
    if ("TracingConfig" in fct_data.keys()) :
        client_regional.update_function_configuration(FunctionName=function_name, TracingConfig = fct_data["TracingConfig"])
    if ("Tags" in fct_data.keys()) :
        client_regional.update_function_configuration(FunctionName=function_name, Tags = fct_data["Tags"])
    
# CREATE A FUNCTION FROM AN OTHER   
def create_bucket_name_check(TEMP_BUCKET,REGION):
    
    # -- Alias -- #
    s3 = boto3.client('s3', region_name=REGION)
    
    NEW_TEMP_BUCKET = TEMP_BUCKET + "-" +addRandom(10)
    try:
        response = s3.create_bucket(
            Bucket= NEW_TEMP_BUCKET,
            CreateBucketConfiguration={'LocationConstraint': REGION }
        )
    except s3.exceptions.BucketAlreadyExists as e:
        NEW_TEMP_BUCKET = create_bucket_name_check(TEMP_BUCKET,REGION)
    except s3.exceptions.BucketAlreadyOwnedByYou as e:
        warnings = NEW_TEMP_BUCKET + " BucketAlreadyOwnedByYou, it will be reused \n"
    
    return NEW_TEMP_BUCKET

def addRandom(length) :
    letters = 'abcdefghijklmnopqrstuvwxyz123456789'
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

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