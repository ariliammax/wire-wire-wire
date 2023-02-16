# main.py
# in chat.wire.server

from chat.common.config import Config
from chat.common.models import Account, Message  # noqa
from chat.common.operations import Opcode
from chat.common.server.events import main as server_main  # noqa
from chat.wire.server.database import Database

import socket
import threading


def entry(**kwargs):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((Config.HOST, Config.PORT))


def handle_connection(connection):
    username = None
    try:
        # TODO: maybe if two devices same acc (out of spec, cf Ed)
        # then just check the db to see if still exists each loop.
        # hacks work ya know.
        while True:
            request = connection.recv(1024).decode("utf-8")
            if len(request) == 0:
                # TODO: I believe this can be a signal of disconnect?
                # and so if we had a notion of state and username, we should
                # update `._logged_in`...
                break

            arguments = request.split(",")
            opcode = int(arguments[0])
            response = " "

            if opcode == Opcode.CREATE_ACCOUNT.value:
                username = arguments[1]
                if username in Database.accounts:
                    response = ' '
                    #  (f'ERROR: Account {username!s} already '
                    #   f'exists... logging in!')

                account = Account()
                account._username = username
                account._logged_in = True
                Database.accounts[username] = account
            elif opcode == Opcode.LIST_ACCOUNTS.value:
                response = ",".join(f'{acc._username!s} '
                                    f'({"in" if not acc._logged_in else ""!s}'
                                    f'active)'
                                    for _, acc in Database.accounts.items())
            elif opcode == Opcode.DELETE_ACCOUNT.value:
                if username in Database.accounts:
                    Database.accounts.pop(username)
                    break

            connection.sendall(response.encode("utf-8"))
    except Exception:
        pass

    if username is not None:
        if username in Database.accounts:
            account = Database.accounts[username]
            account._logged_in = False
            Database.accounts[username] = account


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
