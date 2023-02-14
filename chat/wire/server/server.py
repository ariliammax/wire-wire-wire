import socket

import threading

HOST = "10.250.25.88"
PORT = 8080
TIMEOUT = 1


class A:
    def __init__(self):
        self.a = 0

    def update(self):
        self.a += 1


theA = A()


def handle_connection(connection, address):
    print(theA.a)
    theA.update()
    data = connection.recv(1024)

    import time
    time.sleep(2)
    print(theA.a)
    if not data:
        print("TEST")
    connection.sendall(data)



with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    s.settimeout(TIMEOUT)
    threads = []
    while True:
        try:
            connection, address = s.accept()
            # handle_connection(connection, address)
            thread = threading.Thread(target=handle_connection, args=[connection, address])
            thread.start()
            threads.append(thread)
        except TimeoutError:
            pass
    s.settimeout(None)
