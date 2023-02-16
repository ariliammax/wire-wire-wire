# main.py
# in chat.wire.server

from chat.common.config import Config
from chat.common.operations import Opcode
from chat.common.server.events import main as server_main
from chat.wire.server.database import Database

import socket
import threading


def entry(**kwargs):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((Config.HOST, Config.PORT))


def handle_connection(connection):
    while True:
        request = connection.recv(1024).decode("utf-8")
        response = " "

        arguments = request.split(",")
        if len(arguments[0]) == 0:
            # TODO: I believe this can be a signal of disconnect?
            continue

        opcode = int(arguments[0])

        if opcode == Opcode.CREATE_ACCOUNT.value:
            username = arguments[1]
            if username in Database.accounts:
                response = f"ERROR: Account {username!s} already exists... logging in"
            else:
                Database.accounts.append(username)
        elif opcode == Opcode.LIST_ACCOUNTS.value:
            response = ",".join(Database.accounts)

        connection.sendall(response.encode("utf-8"))


def handler(err: Exception, s: socket.socket = None, **kwargs):
    if s is not None:
        s.shutdown()
        s.close()
    raise err


if __name__ == '__main__':
    # server_main(entry=entry,
    #             # prethread ?
    #             # spawn ?
    #             # handle (attached to spawned thread)
    #             handler=handler)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((Config.HOST, Config.PORT))
        s.listen()
        threads = []
        while True:
            try:
                s.settimeout(Config.TIMEOUT)
                connection, _ = s.accept()
                s.settimeout(None)
                thread = threading.Thread(target=handle_connection,
                                          args=[connection])
                thread.start()
                threads.append(thread)
            except TimeoutError:
                pass
