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


def request(opcode: Opcode, *args, s: socket.socket = None, **kwargs):
    arguments = [opcode.value] + list(args)
    arguments = [str(argument) for argument in arguments]

    request = ",".join(arguments)
    s.sendall(request.encode("utf-8"))

    response = s.recv(1024).decode("utf-8")
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
