import socket

HOST = "10.250.25.88"
PORT = 8080

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"Hello world")
    data = s.recv(1024)
    data = data.decode("utf-8")

print(f"Recv-ed {data!r}")
