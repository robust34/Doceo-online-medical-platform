import json
import time
import boto3
import os
from uuid import uuid4, NAMESPACE_URL
from urllib.parse import urlparse
import stream_chat

def transcribe_file(file_uri, bucket, transcribe_client):

    job_name = str(uuid4())
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': file_uri},
        MediaFormat='mp4',
        LanguageCode='ja-JP',
        OutputBucketName=bucket,
        OutputKey='public/video/'
    )

    # max_tries = 60
    # while max_tries > 0:
    #     max_tries -= 1
    #     job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
    #     print(job)
    #     job_status = job['TranscriptionJob']['TranscriptionJobStatus']
    #     if job_status in ['COMPLETED', 'FAILED']:
    #         print(f"Job {job_name} is {job_status}.")
    #         if job_status == 'COMPLETED':
    #             print(
    #                 f"Download the transcript from\n"
    #                 f"\t{job['TranscriptionJob']['Transcript']['TranscriptFileUri']}.")
    #         break
    #     else:
    #         print(f"Waiting for {job_name}. Current status is {job_status}.")
    #     time.sleep(10)

def send_message(job_name, transcribe_client):
    s3 = boto3.client('s3')

    # Get Transcription Job
    job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
    job_status = job['TranscriptionJob']['TranscriptionJobStatus']
    if job_status in ['COMPLETED', 'FAILED']:
        print(f"Job {job_name} is {job_status}.")
        if job_status == 'COMPLETED':
            print(
                f"Download the transcript from\n"
                f"\t{job['TranscriptionJob']['Transcript']['TranscriptFileUri']}.")
    else:
        return print(f"Waiting for {job_name}. Current status is {job_status}.")

    media_url = urlparse(job['TranscriptionJob']['Media']['MediaFileUri'])
    caption_url = urlparse(job['TranscriptionJob']['Transcript']['TranscriptFileUri'])
    caption_bucket, caption_key = caption_url.path.split('/', 2)[1:]
    media = s3.get_object(
        Bucket=media_url.netloc,
        Key=media_url.path[1:]
    )
    caption = s3.get_object(
        Bucket=caption_bucket,
        Key=caption_key
    )
    user_id = media['Metadata']['userid']
    channel_id = media['Metadata']['channelid'].split(':', 1)[1]
    msgid = media['Metadata']['msgid']
    publish = media['Metadata']['publish']
    caption_data = json.loads(caption['Body'].read())

    if publish == 'false':
        boolPublish = False
    elif publish == 'true':
        boolPublish = True
    else:
        boolPublish = False

    # Send message with uploaded video
    server_client = stream_chat.StreamChat(
        api_key=os.environ['STREAM_KEY'], api_secret=os.environ['STREAM_SECRET'])
    channel = server_client.channel('channel-2', channel_id)
    channel.send_message({
        "text": caption_data["results"]['transcripts'][0]['transcript'],
        "show_in_channel": False,
        "parent_id": msgid,
        "publish": boolPublish,
        "attachments": [
            {
                "type": "video",
                "asset_url": "https://s3-%s.amazonaws.com/%s/%s" % (os.environ['REGION'], media_url.netloc, media_url.path[1:])
            }
        ]
    }, user_id)


def handler(event, context):
    print('received event:')
    # print(event)

    s3Info = event['Records'][0]['s3']

    transcribe_client = boto3.client('transcribe')
    if s3Info['object']['key'][-3:] == 'mp4':
        transcribe_file('s3://' + s3Info['bucket']['name'] + '/' + s3Info['object']['key'], s3Info['bucket']['name'], transcribe_client)
    elif s3Info['object']['key'][-4:] == 'json':
        send_message(s3Info['object']['key'].replace('public/video/', '')[:-5], transcribe_client)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps('Hello from your new Amplify Python lambda!')
    }
