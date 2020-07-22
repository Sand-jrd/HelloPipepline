import json
import ast
import boto3

def lambda_handler(event, context):
    
    # -- Variables -- #
    region         = event['REGION']
    SOURCE_BUCKET  = event['SOURCE_BUCKET']
    ACCOUNT_ID     = event['ACCOUNT_ID']
    SB_REGION      = event['SB_REGION']
    date           = event['DATE']
    TOPIC_SNS      = event['TOPIC_SNS']
    sucess         = event['SUCCESS']
    snsmsg         = event['snsmsg']
    args           = event['Payload']
    
    s3r = boto3.resource('s3', region_name=SB_REGION)

    try:
        content_object = s3r.Object(SOURCE_BUCKET, "logs/log"+date+".txt")
        file_content = content_object.get()['Body'].read().decode('utf-8')
    except Exception as e :
        print("Impossible to write in Logs ... or it doesn't exit : " + str(e))
        file_content = "A probleme occured in the creating of this logs"
    
    file = open("/tmp/logs.txt", "w")
    
    file.write(file_content)
    file.write("Result of " + region + " : \n")
    if sucess :
        if len(args) > 1 :
            file.write("<!WARNING!> " + str(args[1]) + "\n")
        file.write("Version " + str(args[0]) +" deploy sucessfuly")
    else : 
        file.write("<!ERROR!> " + str(args[0]))
    file.write("\n------------------------------------------------- \n")    
    file.close()
    
    s3 = boto3.client('s3', region_name=SB_REGION)
    
    try :
        response = s3.upload_file("/tmp/logs.txt", SOURCE_BUCKET, "logs/log"+date+".txt")
    except : 
        pass
    
    if snsmsg :
        file = open("/tmp/logs.txt", "r")
        sendSNS(SB_REGION,ACCOUNT_ID,TOPIC_SNS,file.read())
        file.close()
        
    return {
        'statusCode'    : 200,
        'body'          : "Send !"
    }
    

# ------------- Tools ------------------- #
        
#Tool for sending e-mail
def sendSNS(SB_REGION,ACCOUNT_ID,TOPIC_SNS,msg):
    
    clientSNS = boto3.client('sns')
    
    response = clientSNS.publish(
        TopicArn = 'arn:aws:sns:'+SB_REGION+':'+ACCOUNT_ID+':'+TOPIC_SNS,
        Message  = msg,
        Subject  = TOPIC_SNS
    )

    