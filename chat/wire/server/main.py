# main.py
# in chat.wire.server

from chat.common.args import parse_server_args as parse_args
from chat.common.config import Config
from chat.common.models import (
    BaseRequest,
    AcknowledgeMessagesRequest,
    CreateAccountRequest,
    DeleteAccountRequest,
    DeliverUndeliveredMessagesRequest,
    ListAccountsRequest,
    LogInAccountRequest,
    LogOutAccountRequest,
    SendMessageRequest,
)
from chat.common.operations import Opcode
from chat.common.server.events import Events, EventsRouter
from typing import Optional

import socket
import threading


def entry(**kwargs):
    """Start the socket for the server.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(Config.ADDRESSES[0])


def handle_connection(connection, **kwargs):
    """The steady state of the server once a connection is established.
    """
    username = None
    try:
        # TODO: maybe if two devices same acc (out of spec, cf Ed)
        # then just check the db to see if still exists each loop.
        # hacks work ya know.
        while True:
            request = connection.recv(1024)
            if len(request) == 0:
                # This is a signal of disconnect.
                # and so if we update `._logged_in` on the loop exit
                break

            event_kwargs = {}
            opcode = Opcode(BaseRequest.peek_opcode(request))

            if kwargs.get('verbose', False):
                print(f'{opcode.name!s} request: {len(request)!s}B.')

            match opcode:
                case Opcode.LOG_IN_ACCOUNT:
                    req = CreateAccountRequest.deserialize(request)
                    event_kwargs['username'] = req.get_username()
                case Opcode.CREATE_ACCOUNT:
                    req = LogInAccountRequest.deserialize(request)
                    event_kwargs['username'] = req.get_username()
                case Opcode.LIST_ACCOUNTS:
                    req = ListAccountsRequest.deserialize(request)
                    event_kwargs['text_wildcard'] = req.get_text_wildcard()
                case Opcode.SEND_MESSAGE:
                    req = SendMessageRequest.deserialize(request)
                    event_kwargs['message'] = req.get_message()
                    event_kwargs['recipient_username'] = \
                        req.get_recipient_username()
                    event_kwargs['sender_username'] = req.get_sender_username()
                case Opcode.DELIVER_UNDELIVERED_MESSAGES:
                    req = DeliverUndeliveredMessagesRequest.deserialize(
                        request)
                    event_kwargs['logged_in'] = req.get_logged_in()
                    event_kwargs['username'] = req.get_username()
                case Opcode.DELETE_ACCOUNT:
                    req = DeleteAccountRequest.deserialize(request)
                    event_kwargs['username'] = req.get_username()
                case Opcode.LOG_OUT_ACCOUNT:
                    req = LogOutAccountRequest.deserialize(request)
                    event_kwargs['username'] = req.get_username()
                case Opcode.ACKNOWLEDGE_MESSAGES:
                    req = AcknowledgeMessagesRequest.deserialize(
                        request)
                    event_kwargs['messages'] = req.get_messages()

            response = EventsRouter[opcode](**event_kwargs)
            res_packet = response.serialize()

            if kwargs.get('verbose', False):
                print(f'{opcode.name!s} response: {len(res_packet)!s}B.')
            connection.sendall(res_packet)
    except Exception as e:
        raise e

    if username is not None:
        # update the logged in status... don't check for multiple devices
        Events.log_out_account(username=username)


def handler(err: Exception, s: Optional[socket.socket] = None, **kwargs):
    """Handle errors if they come up. i.e. close the socket.
    """
    if s is not None:
        s.shutdown()
        s.close()
    raise err


def main(machine_id=0, **kwargs):
    """Start a server and keep on listening.
    """
    Events.startup(machine_id=machine_id)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(Config.ADDRESSES[machine_id])
        s.listen()
        s.settimeout(Config.TIMEOUT_CLIENT)
        threads = []
        while True:
            try:
                connection, _ = s.accept()
                thread = threading.Thread(target=handle_connection,
                                          args=[connection],
                                          kwargs=kwargs)
                thread.start()
                threads.append(thread)
            except TimeoutError:
                pass


if __name__ == '__main__':
    main(**parse_args().__dict__)
