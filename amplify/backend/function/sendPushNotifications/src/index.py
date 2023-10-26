import json
import time
import os
import boto3
from botocore.exceptions import ClientError
import stream_chat

def handler(event, context):
    print(event)
    server_client = stream_chat.StreamChat(
        api_key=os.environ['STREAM_KEY'], api_secret=os.environ['STREAM_SECRET'])
    type = event['arguments']['type']
    text = event['arguments']['text']

    users = server_client.query_users({'role': 'user'}, None, limit=100)
    allowed_users = filter(lambda user: not ( 'disable_notifciation' in user.keys() and user['disable_notifciation'] == 'yes'), users['users'] )

    # Environment
    app_id = os.environ['ANALYTICS_DOCEONEW_ID']
    client = boto3.client('pinpoint',region_name=os.environ['ANALYTICS_DOCEONEW_REGION'])
    content = json.dumps({
        "notification": {
            "title": "運営からのお知らせ",
            "body": """{
                "message": "{text}",
                "role": "admin",
                "image": ""
            }"""
        },
        "data": {
            "type": type
        }
    })
    addresses = {}
    for user in allowed_users:
        devices = server_client.get_devices(user['id'])
        for device in devices['devices']:
            if not ( 'disabled' in device.keys() and device['disabled'] == True ):
                addresses[device['id']] = {
                    'ChannelType': 'GCM'
                }

    try:
        message_request = {
            'Addresses': addresses,
            'MessageConfiguration': {
                'GCMMessage': {
                    'Action': 'OPEN_APP',
                    'RawContent': content
                }
            }
        }
        client.send_messages(
            ApplicationId=app_id,
            MessageRequest=message_request
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
        return False

    return True
