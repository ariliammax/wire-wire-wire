# main.py
# in chat.wire.server

from chat.common.config import Config
from chat.common.operations import Opcode
from chat.common.server.events import Events, EventsRouter
from typing import Optional

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
            request = connection.recv(1024).decode('utf-8')
            if len(request) == 0:
                # This is a signal of disconnect.
                # and so if we update `._logged_in` on the loop exit
                break

            args = request.split(',')
            kwargs = {}
            opcode = Opcode(int(args[0]))

            match opcode:
                case Opcode.CREATE_ACCOUNT:
                    kwargs['username'] = args[1]
                case Opcode.LIST_ACCOUNTS:
                    pass
                case Opcode.SEND_MESSAGE:
                    kwargs['message'] = args[1]
                    kwargs['recipient_username'] = args[2]
                    kwargs['sender_username'] = username
                case Opcode.DELIVER_UNDELIVERED_MESSAGES:
                    kwargs['username'] = username
                case Opcode.DELETE_ACCOUNT:
                    kwargs['username'] = username

            response = EventsRouter[opcode](**kwargs)

            connection.sendall(response.encode('utf-8'))
    except Exception:
        pass

    if username is not None:
        # update the logged in status... don't check for multiple devices
        Events.account_logout(username=username)


def handler(err: Exception, s: Optional[socket.socket] = None, **kwargs):
    if s is not None:
        s.shutdown()
        s.close()
    raise err


def main():
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


if __name__ == '__main__':
    main()
