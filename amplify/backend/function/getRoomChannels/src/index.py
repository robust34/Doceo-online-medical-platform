import json
import stream_chat


def handler(event, context):
    server_client = stream_chat.StreamChat(
        api_key="a6rmt92za3p7", api_secret="jx9tp9jcc3f4b6j8732zynqf7byu4tfbjjah266hskgz7h8vnwngfrpzcg2mddwg")
    channels = server_client.query_channels(
        {'room': event['arguments']['room_id']})

    return channels['channels']
