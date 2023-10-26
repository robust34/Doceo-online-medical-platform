import json
import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import stream_chat

def get_message(user, room, msg):
    link = 'https://doceo-dr-mobile-stg.doceo.link/#/Home/AnswerQuestion/%s' % msg['id']
    if 'birthday' in user:
        delta = relativedelta(datetime.now(), datetime.strptime(user['birthday'], '%Y-%m-%d'))
        patient = "%s代 %s" % int(delta.years / 10) * 10, ('sex' in user if user['sex'] else '男性')
    else:
        patient = "年代不明"

    return f"""<html>
    <head></head>
    <body>
      <p>
        「({patient}) <{room['name']}> [{msg['text']}]」回答するにはこちらをクリック
        <br/> <a href="{link}">{link}</a>
    </body>
    </html>
    """

def send_message(to_addresses, char_set, subject, message):
    pinpoint_client = boto3.client('pinpoint-email')

    try:
        response = pinpoint_client.send_email(
            FromEmailAddress='info@wivil.co.jp',
            Destination={'ToAddresses': to_addresses},
            Content={
            'Simple': {
                'Subject': {'Charset': char_set, 'Data': subject},
                'Body': {
                    'Html': {'Charset': char_set, 'Data': message},
                    # 'Text': {'Charset': char_set, 'Data': text_message}
                }
            }
            }
        )
    except ClientError:
        print("The message wasn't sent")
        raise
    else:
        return response['MessageId']

def handler(event, context):
    print('received event:')
    print(event)

    if type(event['Records'][0]['body']) is str:
        msg_info = json.loads(event['Records'][0]['body'])
    else:
        msg_info = event['Records'][0]['body']

    user_id = msg_info["user"]["id"]
    server_client = stream_chat.StreamChat(
        api_key=os.environ['STREAM_KEY'], api_secret=os.environ['STREAM_SECRET'])

    # user_info = cognito.admin_get_user(
    #     UserPoolId = os.environ['AUTH_DOCEONEW9D5671B29D5671B2_USERPOOLID'],
    #     Username = user_id
    # )

    if msg_info['type'] == 'message.new' and msg_info['channel_type'] == 'channel-2' and msg_info['user']['role'] == 'user' :
        channel = server_client.query_channels(
            {
                'type': 'channel-2',
                'id': msg_info['channel_id']
            },
            {},
            limit=1
        )['channels'][0]
        # print(channel['channel']['room'])
        room = server_client.query_channels(
            {
                'type': 'room',
                'id': channel['channel']['room']
            },
            {},
            limit=1
        )['channels'][0]
        # print(room['members'])
        doctors = filter( lambda member: member['user']['role'] == 'doctor', room['members'] )
        doctor_ids = map( lambda doctor: doctor['user_id'], doctors )
        # print(list(doctor_ids))
        # print(list(doctors))
        cognito = boto3.client('cognito-idp')
        doctor_emails = []
        for id in doctor_ids:
            result = cognito.list_users(
                UserPoolId=os.environ['AUTH_DOCEONEW9D5671B29D5671B2_USERPOOLID'],
                AttributesToGet=['email'],
                Filter="sub = '%s'" % id
            )
            if len(result['Users']) > 0 and len(result['Users'][0]['Attributes']) > 0:
                doctor_emails.append(result['Users'][0]['Attributes'][0]['Value'])

        # results = cognito.list_users(
        #     UserPoolId=os.environ['AUTH_DOCEONEW9D5671B29D5671B2_USERPOOLID'],
        #     AttributesToGet=['email'],
        #     Filter="sub = 'e0e07a6a-ee1a-44ca-9e75-8ec25a9a8ff1'"
        # )
        # doctor_emails = list( map( lambda doctor: doctor['Attributes'][0]['Value'], results['Users'] ) )
        # doctor_emails = ['talentservice129@gmail.com']
        subject = "新しい質問が投稿されました。Doceoにログインしてご確認ください。"
        message = get_message(msg_info['user'], room['channel'], msg_info['message'])
        send_message(doctor_emails, 'UTF-8', subject, message)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps('Hello from your new Amplify Python lambda!')
    }