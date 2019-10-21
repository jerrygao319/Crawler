import socket

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
    while i < 999:
        resp = sock.recv(2048).decode("utf-8")
        if resp.startswith("PING"):
            print("PING:", resp)
        else:
            print("Received:", repr(resp))
        i += 1
except Exception:
    print("Error")
finally:
    sock.close()

