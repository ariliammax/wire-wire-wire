# main.py
# in chat.wire.client

#from chat.common.config import Config
class Config:
    HOST = "10.250.25.88"
    PORT = 8080
    TIMEOUT = 1

from enum import Enum
class Opcode(Enum):
    LOGIN_ACCOUNT = 0
    CREATE_ACCOUNT = 1
    LIST_ACCOUNTS = 2
    SEND_MESSAGE = 3
    DELIVER_UNDELIVERED_MESSAGES = 4
    DELETE_ACCOUNT = 5

import socket

if __name__ == '__main__':
    name = input("> Name: ")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((Config.HOST, Config.PORT))

        arguments = []
        arguments.append(Opcode.CREATE_ACCOUNT.value)
        arguments.append(name)
        arguments = [str(argument) for argument in arguments]

        request = ",".join(arguments)
        s.sendall(request.encode("utf-8"))

        response = s.recv(1024).decode("utf-8")
    print(response)
