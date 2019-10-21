import socket
import datetime

config = {
    "server": "irc.chat.twitch.tv",
    "port": 6667,
    "nickname": "renaissancevector",
    "token": "oauth:j4c2ruphbc7v5v3eyhlt12lp1blipy",
    "channel": "#pvpx"
}

sock = socket.socket()
sock.connect((config["server"], config["port"]))

sock.send(f'PASS {config["token"]}\r\n'.encode("utf-8"))
sock.send(f'NICK {config["nickname"]}\r\n'.encode("utf-8"))
sock.send(f'JOIN {config["channel"]}\r\n'.encode("utf-8"))

try:
    i = 0
    while i < 99:
        resp = sock.recv(2048).decode("utf-8")
        if resp.startswith("PING"):
            print("PING:", resp)
        else:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open("twitch_chat_log", 'a') as f:
                f.write(str(now))
                f.write(str(resp))
        i += 1
except Exception:
    print("Error")
finally:
    f.close()
    sock.close()

