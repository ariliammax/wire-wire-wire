# main.py
# in chat.wire.server

#from chat.common.config import Config
class Config:
    HOST = "10.250.25.88"
    PORT = 8080
    TIMEOUT = 1

from database import Database

from enum import Enum
class Opcode(Enum):
    LOGIN_ACCOUNT = 0
    CREATE_ACCOUNT = 1
    LIST_ACCOUNTS = 2
    SEND_MESSAGE = 3
    DELIVER_UNDELIVERED_MESSAGES = 4
    DELETE_ACCOUNT = 5

import socket
import threading

def handle_connection(connection, address):
    while True:
        request = connection.recv(1024).decode("utf-8")
        response = " "

        arguments = request.split(",")
        opcode = int(arguments[0])

        if opcode == Opcode.CREATE_ACCOUNT.value:
            username = arguments[1]
            if username in Database.accounts:
                response = "ERROR"
            else:
                Database.accounts.append(username)
        elif opcode == Opcode.LIST_ACCOUNTS.value:
            response = ",".join(Database.accounts)

        connection.sendall(response.encode("utf-8"))

if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((Config.HOST, Config.PORT))
        s.listen()
        threads = []
        while True:
            try:
                s.settimeout(Config.TIMEOUT)
                connection, address = s.accept()
                s.settimeout(None)
                thread = threading.Thread(target=handle_connection,
                                          args=[connection, address])
                thread.start()
                threads.append(thread)
            except TimeoutError:
                pass
