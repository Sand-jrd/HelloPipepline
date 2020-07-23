import json
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb        = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    
    TABLE_NAME    = "BASCClientList"
    SOURCE_BUCKET = "test-pipeline--layer"
    
    table = dynamodb.Table(TABLE_NAME)
    
    response = dynamodb_client.scan(
        TableName=TABLE_NAME,
        AttributesToGet = ["AWSAccountID","AWSCustomerID"],
        ScanFilter={
            'CurrentStatus': {
                'AttributeValueList': [
                    {
                        'S': 'Subscribed-pending'
                    }
                ],
                'ComparisonOperator': 'EQ'
            }
        }
    )
    
    app_json = json.dumps(response)
    print(app_json)
    
    file = open("/tmp/TestACL.txt", "w")
    file.write(app_json)
    file.close()
    
    
    response = s3.upload_file("/tmp/TestACL.txt", SOURCE_BUCKET, "TestACL.txt")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Sucsfull converted')
    }
