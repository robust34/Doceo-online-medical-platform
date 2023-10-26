import json
import stream_chat


def handler(event, context):
    server_client = stream_chat.StreamChat(
        api_key="a6rmt92za3p7", api_secret="jx9tp9jcc3f4b6j8732zynqf7byu4tfbjjah266hskgz7h8vnwngfrpzcg2mddwg")
    token = server_client.create_token(event['arguments']['id'])
    channels = server_client.query_channels({'type': 'room'})

    return {
        'token': token,
        'rooms': channels['channels']
    }
