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

def request(opcode: Opcode, *args, **kwargs):
    arguments = [opcode.value] + list(args)
    arguments = [str(argument) for argument in arguments]

    request = ",".join(arguments)
    s.sendall(request.encode("utf-8"))

    response = s.recv(1024).decode("utf-8")
    return response

if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((Config.HOST, Config.PORT))

        username = input("> Username: ")

        response = request(Opcode.CREATE_ACCOUNT, username)
        print(response)

        while True:
            print(
                (
                    "Do you want to...\n"
                    "1) List Accounts\n"
                    "2) Send a Message\n"
                    "3) Deliver Undelivered Messages\n"
                    "4) Delete Account\n"
                )
            )
            opcode = input("> 1/2/3/4: ")
            opcode = int(opcode) + 1
            if (opcode == Opcode.LIST_ACCOUNTS.value):
                response = request(Opcode.LIST_ACCOUNTS)
                print("\nAccounts:\n[" + response + "]\n")
            elif (opcode == Opcode.SEND_MESSAGE.value):
                break
            elif (opcode == Opcode.DELIVER_UNDELIVERED_MESSAGES.value):
                break
            elif (opcode == Opcode.DELETE_ACCOUNT.value):
                break
