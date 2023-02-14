import socket

HOST = "104.28.39.32"
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"Hello world")
    data = s.recv(1024)
    data = data.decode("utf-8")

print(f"Recieved {data!r}")
