from chat.common.config import Config

import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((Config.HOST, Config.PORT))
    s.sendall(b"Hello world")
    data = s.recv(1024)
    data = data.decode("utf-8")

print(f"Recv-ed {data!r}")
