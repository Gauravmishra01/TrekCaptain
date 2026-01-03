import boto3

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
try:
    table = dynamodb.Table('OTPVerification')
    table.delete()
    print('Table OTPVerification deleted')
    table.meta.client.get_waiter('table_not_exists').wait(TableName='OTPVerification')
    print('Table deleted successfully')
except Exception as e:
    print(f'Error: {e}')