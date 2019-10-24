import socket
import datetime
import re

config = {
    "server": "irc.chat.twitch.tv",
    "port": 6667,
    "nickname": "renaissancevector",
    "token": "oauth:j4c2ruphbc7v5v3eyhlt12lp1blipy",
    "channel": "#starcraft"
}

sock = socket.socket()
sock.connect((config["server"], config["port"]))

sock.send(f'PASS {config["token"]}\r\n'.encode("utf-8"))
sock.send(f'NICK {config["nickname"]}\r\n'.encode("utf-8"))
sock.send(f'JOIN {config["channel"]}\r\n'.encode("utf-8"))

username = ""
comment = ""
channel = ""
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
                regex = r":(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG ##([^:]*) :(.*)"
                username, channel, comment = re.search(regex, respSingle, re.IGNORECASE).groups()
                with open("twitch_chat_log_191024.log", 'a+') as f:
                    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write("%s\t%s\t%s\t%s\n" % (nowTime, channel, username, comment))

except Exception as e:
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " Error:", e)
finally:
    sock.close()
    f.close()
