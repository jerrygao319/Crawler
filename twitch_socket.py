import socket
import datetime

config = {
    "server": "irc.chat.twitch.tv",
    "port": 6667,
    "nickname": "renaissancevector",
    "token": "oauth:j4c2ruphbc7v5v3eyhlt12lp1blipy",
    "channel": "#myth"
}

sock = socket.socket()
sock.connect((config["server"], config["port"]))

sock.send(f'PASS {config["token"]}\r\n'.encode("utf-8"))
sock.send(f'NICK {config["nickname"]}\r\n'.encode("utf-8"))
sock.send(f'JOIN {config["channel"]}\r\n'.encode("utf-8"))

try:
    while True:
        resp = sock.recv(2048).decode("utf-8")
        if resp.startswith("PING"):
            print("PING:", resp)
        else:
            print("Received:", resp)
            with open("twitch_chat_log_191023.log", 'a') as f:
                f.write(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                f.write(str(resp))
except Exception:
    print("Error")
finally:
    f.close()
    sock.close()

