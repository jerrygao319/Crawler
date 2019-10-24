import socket
import datetime
import re

config = {
    "server": "irc.chat.twitch.tv",
    "port": 6667,
    "nickname": "renaissancevector",
    "token": "oauth:j4c2ruphbc7v5v3eyhlt12lp1blipy",
    "channel": "#nickmercs"
}

sock = socket.socket()
sock.connect((config["server"], config["port"]))

sock.send(f'PASS {config["token"]}\r\n'.encode("utf-8"))
sock.send(f'NICK {config["nickname"]}\r\n'.encode("utf-8"))
sock.send(f'JOIN {config["channel"]}\r\n'.encode("utf-8"))

username = ""
comment = ""
try:
    while True:
        resp = sock.recv(2048).decode("utf-8")
        if not resp:
            break
        if resp.startswith("PING"):
            print("PING: ", resp)
        elif resp.startswith(":tmi.twitch.tv"):
            print("HEADER: ", resp)
        else:
            print("Received: ", resp)
            respList = resp.splitlines()
            for respSingle in respList:
                if respSingle.startswith(":" + config["nickname"]):
                    continue
                infoList = respSingle.split(config["channel"])
                usernameInfoList = infoList[0].split(":")
                if len(usernameInfoList) >= 2:
                    username_search = re.search(r"(.*)!.*@(.*) ", usernameInfoList[1], re.IGNORECASE)
                    if username_search:
                        username = username_search.group(1)
                        userURL = username_search.group(2)
                if len(infoList) >= 2:
                    comment = infoList[1].split(":")[1]
                with open("twitch_chat_log_191024.log", 'a+') as f:
                    f.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "\t")
                    f.write(username, "\t", comment, "\n")

except Exception as e:
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " Error:", e)
finally:
    f.close()
    sock.close()
