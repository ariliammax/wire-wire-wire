# events.py
# in chat.common.client.shiny

from chat.common.config import Config
from chat.common.operations import Opcode
from typing import Callable

import datetime
import threading

import curses


timer = None


def initscr(**kwargs):
    scr = curses.initscr()

    # get the size of the screen
    rows, cols = scr.getmaxyx()

    # create the two windows
    header_height, header_width, header_y, header_x = 3, cols, 0, 0
    header_win = curses.newwin(header_height,
                               header_width,
                               header_y,
                               header_x)

    term_border_height, \
        term_border_width, \
        term_border_y, \
        term_border_x = 15, cols, 3, 0
    term_border_win = curses.newwin(term_border_height,
                                    term_border_width,
                                    term_border_y,
                                    term_border_x)

    term_height, term_width = term_border_height - 2, term_border_width - 2
    term_y, term_x = term_border_y + 1, term_border_x + 1
    term_win = curses.newwin(term_height, term_width, term_y, term_x)

    term_out_height, term_out_width, term_out_y, term_out_x = 3, cols, 18, 0
    term_out_win = curses.newwin(term_out_height,
                                 term_out_width,
                                 term_out_y,
                                 term_out_x)

    msg_border_height, \
        msg_border_width, \
        msg_border_y, \
        msg_border_x = rows-21, cols, 21, 0
    msg_border_win = curses.newwin(msg_border_height,
                                   msg_border_width,
                                   msg_border_y,
                                   msg_border_x)

    msg_height, msg_width = msg_border_height - 2, msg_border_width - 2
    msg_y, msg_x = msg_border_y + 1, msg_border_x + 1
    msg_win = curses.newwin(msg_height, msg_width, msg_y, msg_x)

    # turn on scrolling
    term_win.scrollok(True)
    msg_win.scrollok(True)

    # pass to kwargs
    kwargs['header_win'] = header_win
    kwargs['header_width'] = header_width
    kwargs['term_border_win'] = term_border_win
    kwargs['term_out_win'] = term_out_win
    kwargs['term_win'] = term_win
    kwargs['msg_border_win'] = msg_border_win
    kwargs['msg_win'] = msg_win

    return kwargs


def initialize_curses(header_win=None,
                      term_win=None,
                      term_border_win=None,
                      term_out_win=None,
                      header_width=None,
                      **kwargs):
    term_win.keypad(0)
    curses.echo()

    # turn on color mode
    curses.start_color()

    # define color pairs
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)

    # Print the text in the center of the window
    header_str = "WELCOME TO CHATMAN 262"
    header_win.addstr(1, header_width // 2 - len(header_str) // 2, header_str)

    header_win.box()
    header_win.noutrefresh()

    term_border_win.box()
    term_border_win.noutrefresh()

    term_out_win.box()
    term_out_win.noutrefresh()

    curses.doupdate()


def clear_term_window(term_win=None, **kwargs):
    term_win.clear()
    term_win.noutrefresh()
    term_win.move(0, 0)
    curses.doupdate()


def print_to_term_out(msg, color, term_out_win=None, **kwargs):
    term_out_win.clear()
    term_out_win.box()
    if color == "red":
        term_out_win.addstr(1, 1, msg, curses.color_pair(1))
    elif color == "green":
        term_out_win.addstr(1, 1, msg, curses.color_pair(2))
    else:
        term_out_win.addstr(1, 1, msg)

    term_out_win.noutrefresh()
    curses.doupdate()


def print_messages(messages=None,
                   term_win=None,
                   msg_win=None,
                   **kwargs):
    """Prints some `Message`s to the console.
    """
    formatted_messages = ""

    # Create a dictionary to group messages by sender
    grouped_messages = {}
    for message in messages:
        sender = message.get_sender_username()
        if sender in grouped_messages:
            grouped_messages[sender].append((message.get_time(),
                                             message.get_message()))
        else:
            grouped_messages[sender] = [(message.get_time(),
                                         message.get_message())]

    # Iterate over the grouped messages and format them
    for sender, messages in grouped_messages.items():
        messages.sort(key=lambda t_msg: t_msg[0])
        formatted_messages += f'\n> {sender}\n'
        for t, message in messages:
            formatted_messages += (datetime.datetime.fromtimestamp(t)
                                   .isoformat(sep=' '))
            formatted_messages += f' {message}\n'

    # Remove the trailing newline character
    formatted_messages = formatted_messages.lstrip()

    term_y, term_x = term_win.getyx()
    msg_win.addstr(formatted_messages)
    msg_win.noutrefresh()
    term_win.move(term_y, term_x)
    term_win.noutrefresh()
    curses.doupdate()


def poll(request: Callable = None, username: str = None, **kwargs):
    """Performs a regular `DeliverUndeliveredMessagesRequest` (followed by
        a `AcknowledgeMessagesRequest`.
    """
    response = request(opcode=Opcode
                       .DELIVER_UNDELIVERED_MESSAGES,
                       logged_in=True,
                       username=username,
                       **kwargs)
    if response.get_error() == '':
        messages = response.get_messages()

        # ack the messages
        _ = request(opcode=Opcode
                    .ACKNOWLEDGE_MESSAGES,
                    messages=messages,
                    **kwargs)

        print_messages(messages=messages, **kwargs)

    create_poll(request=request, username=username, **kwargs)


def create_poll(request: Callable = None, username: str = None, **kwargs):
    """Creates the background polling `threading.Timer` that will execute
        `poll`.
    """
    global timer
    timer = threading.Timer(interval=Config.POLL_TIME,
                            function=poll,
                            kwargs=dict(request=request,
                                        username=username,
                                        **kwargs))
    timer.start()


def main(entry: Callable, request: Callable, handler: Callable, **kwargs):
    """A nice (TM) generic way of handling the event logic shared by the wire
       and gRPC protocols.
       `entry` is called once at the beginning, to establish the connection
        (or whatever other setup you want to do). Note that `kwargs` will be
        set to the return value of `entry` here, so it can pass the connections
        onwards to `request` and `handler`.
       `request` does requests across the connection,
       `handler` handles errors.
    """
    try:
        kwargs = entry(**kwargs)
        has_logged_in = False
        kwargs = initscr(**kwargs)
        initialize_curses(**kwargs)

        term_win = kwargs.get('term_win', None)
        msg_border_win = kwargs.get('msg_border_win', None)

        while not has_logged_in:
            clear_term_window(**kwargs)
            term_win.addstr(
                'Do you want to...\n'
                '1) Log In\n'
                '2) Signup\n')
            term_win.addstr('> ')
            opcode = term_win.getstr().decode()

            if opcode not in [str(i + 1) for i in range(2)]:
                print_to_term_out("Invalid input.",
                                  "red",
                                  **kwargs)
                continue

            # - 1 since Opcode.CREATE_ACCOUNT has value 0.
            opcode = Opcode(int(opcode) - 1)
            match opcode:
                case Opcode.LOG_IN_ACCOUNT:
                    term_win.addstr('\n> Username: ')
                    username = term_win.getstr().decode()
                    response = request(opcode=Opcode.LOG_IN_ACCOUNT,
                                       username=username,
                                       **kwargs)
                    if response.get_error() == '':
                        print_to_term_out("Welcome back!",
                                          "green",
                                          **kwargs)
                        has_logged_in = True
                    else:
                        print_to_term_out(f'{response.get_error()!s}',
                                          "red",
                                          **kwargs)
                case Opcode.CREATE_ACCOUNT:
                    term_win.addstr('\n> Username: ')
                    username = term_win.getstr().decode()
                    response = request(opcode=Opcode.CREATE_ACCOUNT,
                                       username=username,
                                       **kwargs)
                    if response.get_error() == '':
                        print_to_term_out("Account creation succesful!",
                                          "green",
                                          **kwargs)
                        has_logged_in = True
                    else:
                        print_to_term_out(f'{response.get_error()!s}',
                                          "red",
                                          **kwargs)

        # start polling for new messages, every
        create_poll(request=request, username=username, **kwargs)

        msg_border_win.box()
        msg_border_win.noutrefresh()

        while True:
            clear_term_window(**kwargs)
            term_win.addstr(
                'Do you want to...\n'
                '1) List Accounts\n'
                '2) Send a Message\n'
                '3) Deliver Undelivered Messages\n'
                '4) Delete Account\n'
                '5) Log Out\n')
            term_win.addstr('> ')
            opcode = term_win.getstr().decode()

            if opcode not in [str(i + 1) for i in range(5)]:
                print_to_term_out("Invalid input.",
                                  "red",
                                  **kwargs)
                continue

            # + 1 since Opcode.[option above] is one more than printed option
            opcode = Opcode(int(opcode) + 1)
            match opcode:
                case Opcode.LIST_ACCOUNTS:
                    term_win.addstr('\n> Text Wildcard: ')
                    text_wildcard = term_win.getstr().decode()
                    response = request(opcode=Opcode.LIST_ACCOUNTS,
                                       text_wildcard=text_wildcard,
                                       **kwargs)
                    accounts = response.get_accounts()
                    formatted_accounts = [f'{account.get_username()} (active: '
                                          f'{account.get_logged_in()}), '
                                          for account in accounts]
                    formatted_account_list = ''.join(formatted_accounts)
                    formatted_account_list = formatted_account_list.rstrip(', ')
                    if response.get_error() == '':
                        if (len(formatted_accounts) == 0):
                            print_to_term_out("No matching accounts found.",
                                          "red",
                                          **kwargs)
                        else:
                            print_to_term_out(f'{formatted_account_list!s}',
                                                "white",
                                                **kwargs)
                    else:
                        print_to_term_out(f'{response.get_error()!s}',
                                          "red",
                                          **kwargs)
                case Opcode.SEND_MESSAGE:
                    term_win.addstr('\n> Recipient: ')
                    recipient = term_win.getstr().decode()
                    term_win.addstr('\n> Message: ')
                    message = term_win.getstr().decode()
                    response = request(
                        opcode=Opcode.SEND_MESSAGE,
                        message=message,
                        recipient_username=recipient,
                        sender_username=username,
                        **kwargs)
                    if response.get_error() == '':
                        print_to_term_out("Your message was sent!",
                                          "green",
                                          **kwargs)
                    else:
                        print_to_term_out(f'{response.get_error()!s}',
                                          "red",
                                          **kwargs)
                case Opcode.DELIVER_UNDELIVERED_MESSAGES:
                    response = request(opcode=Opcode
                                       .DELIVER_UNDELIVERED_MESSAGES,
                                       logged_in=False,
                                       username=username,
                                       **kwargs)
                    if response.get_error() == '':
                        messages = response.get_messages()

                        # ack the messages
                        _ = request(opcode=Opcode
                                    .ACKNOWLEDGE_MESSAGES,
                                    messages=messages,
                                    **kwargs)

                        print_messages(messages=messages, **kwargs)
                    else:
                        print_to_term_out(f'{response.get_error()!s}',
                                          "red",
                                          **kwargs)
                case Opcode.LOG_OUT_ACCOUNT:
                    response = request(opcode=Opcode.LOG_OUT_ACCOUNT,
                                       username=username,
                                       **kwargs)
                    if response.get_error() == '':
                        term_win.addstr('\n""""""""""""""""""""'
                                        '\nGOODBYE FROM CHATMAN'
                                        '\n""""""""""""""""""""\n')
                        break
                    else:
                        print_to_term_out(f'{response.get_error()!s}',
                                          "red",
                                          **kwargs)
                case Opcode.DELETE_ACCOUNT:
                    response = request(opcode=Opcode.DELETE_ACCOUNT,
                                       username=username,
                                       **kwargs)
                    if response.get_error() == '':
                        print_to_term_out("Your message was sent!",
                                          "green",
                                          **kwargs)
                        break
                    else:
                        print_to_term_out(f'{response.get_error()!s}',
                                          "red",
                                          **kwargs)

    except Exception as err:
        handler(err=err, **kwargs)

    if timer is not None:
        timer.cancel()
