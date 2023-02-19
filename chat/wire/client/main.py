# main.py
# in chat.wire.client

from chat.common.client.events import main as client_main
from chat.common.config import Config
from chat.common.operations import Opcode
from typing import Optional

import socket


def entry(**kwargs):
    # with ..
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((Config.HOST, Config.PORT))
    kwargs['s'] = s
    return kwargs


def request(opcode: Opcode,
            s: socket.socket = None,
            username: Optional[str] = None,
            message: Optional[str] = None,
            recipient_username: Optional[str] = None,
            sender_username: Optional[str] = None,
            **kwargs):
    args = []
    match opcode:
        case Opcode.LOGIN_ACCOUNT:
            args.append(username)
        case Opcode.CREATE_ACCOUNT:
            args.append(username)
        case Opcode.LIST_ACCOUNTS:
            pass
        case Opcode.SEND_MESSAGE:
            args += [message, recipient_username, sender_username]
        case Opcode.DELIVER_UNDELIVERED_MESSAGES:
            args.append(username)
        case Opcode.DELETE_ACCOUNT:
            args.append(username)

    arguments = [opcode.value] + args
    arguments = [str(argument) for argument in arguments]

    request = ','.join(arguments)
    s.sendall(request.encode('utf-8'))

    response = s.recv(1024).decode('utf-8')
    return response


def handler(err: Exception, s: Optional[socket.socket] = None, **kwargs):
    if s is not None:
        s.shutdown()
        s.close()
    raise err


if __name__ == '__main__':
    client_main(entry=entry,
                request=request,
                handler=handler)
