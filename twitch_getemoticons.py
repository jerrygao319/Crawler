import requests

headers = {
    'Accept': 'application/vnd.twitchtv.v5+json',
    'Client-ID': 'h2b6x4javlgw1ziehpllkc8ukr9vxd',
}

response = requests.get('https://api.twitch.tv/kraken/chat/emoticon_images', headers=headers)
response.encoding = 'utf-8'
if response:
    try:
        with open("twitch_emoticons_191024.json", 'w+') as f:
            f.write(response.content.decode("utf-8"))
    except Exception as e:
        print(e)
    finally:
        f.close()
else:
    print("Error")
