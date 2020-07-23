import json
import boto3
import ast 
import sys

# This is the Lambda in charge of creating/updating he Lambda test for 
# the deployment of a Layer. 

def lambda_handler(event, context):
    
    # Initialisation
    
    SOURCE_BUCKET  = "test-pipeline-lambdatest"
    jsonConf       = getConf(SOURCE_BUCKET)
    conf           = jsonConf["config"]
    region_list    = jsonConf['region-list']
    default_region = "us-east-1"
    
    # Alias
    s3                     = boto3.client('s3')
    client                 = boto3.client('lambda')
    
    # --- Publish in every listed regions --- #
    

    for dict_region in region_list :
        region = dict_region['region']
        # -- Step one : create a temporay bucket in the targeted region -- # (Skip if delault region)
        print(region)
        if region != default_region :
            
            #Creat a bucket
            TEMP_BUCKET    = SOURCE_BUCKET+"-"+region+"-"+"temporary"
            try :
                response = s3.create_bucket(
                    Bucket                    = TEMP_BUCKET,
                    CreateBucketConfiguration = {'LocationConstraint': region }
                )
            except s3.exceptions.BucketAlreadyExists as e:
                TEMP_BUCKET = create_bucket_name_check(TEMP_BUCKET,region)
            except s3.exceptions.BucketAlreadyOwnedByYou as e:
                warnings = TEMP_BUCKET + " BucketAlreadyOwnedByYou, it will be reused \n"
            
            #Copy all files
            for key in s3.list_objects(Bucket=SOURCE_BUCKET)['Contents']:
                files       = key['Key']
                copy_source = {'Bucket': SOURCE_BUCKET,'Key': files}
                s3.copy(copy_source, TEMP_BUCKET, files)
        else : 
            TEMP_BUCKET = SOURCE_BUCKET
        
        # -- Step two : create/updtae the Test Lambda from template -- #
        
        client_regional = boto3.client('lambda', region_name=region)
        
        try :
            response = client_regional.get_function(FunctionName  = conf['FunctionName'])
        except client_regional.exceptions.ResourceNotFoundException :
            response = client_regional.create_function(
                FunctionName     = conf['FunctionName'],
                Runtime          = conf['Runtime'],
                Role             = conf['Role'],
                Handler          = conf['Handler'],
                Description      = conf['Description'],
                Code = {
                    "S3Bucket": TEMP_BUCKET,
                    "S3Key"   : conf['Code']['S3Key']
		        }
		    )
        except Exception as e :
            raise Exception(str(e))
        else :
            response = client_regional.update_function_code(
                FunctionName     = conf['FunctionName'],
                S3Bucket=TEMP_BUCKET,
                S3Key= conf['Code']['S3Key']
            )
            response = client_regional.update_function_configuration(
                FunctionName     = conf['FunctionName'],
                Runtime          = conf['Runtime'],
                Role             = conf['Role'],
                Handler          = conf['Handler'],
                Description      = conf['Description']
            )
            
        # -- Step three : delete the temporary Bucket -- # (Skip if delault region)
        
        if region != default_region :
            response = delete_bucket_completely(TEMP_BUCKET, region)

     
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }





""" ------------------------ TOOLS  -------------------------- """


# Get content of configuration from Bucke source 
def getConf(SOURCE_BUCKET) :
    
    s3r = boto3.resource('s3')
    json_content = " "
    #Get the client list
    try:
        content_object = s3r.Object(SOURCE_BUCKET, 'Config.json')
    except Exception as e :
       print(str(e))
    
    # Convert file to be read
    try :    
        file_content = content_object.get()['Body'].read().decode('utf-8')
        json_content = json.loads(file_content)
    except Exception as e :
       print(str(e))
       
    return json_content
    
    
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
    
    return TEMP_BUCKET

def addRandom(length) :
    letters = 'abcdefghijklmnopqrstuvwxyz123456789'
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str
    
    
    
    
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