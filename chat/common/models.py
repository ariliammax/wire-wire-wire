# models.py
# in chat.common

from typing import Optional

# DATA MODEL

class Account(object):
    def __init__(self):
        self._logged_in: bool = False
        self._username: str = ""

class Message(object):
    def __init__(self):
        self._delivered: bool = False
        self._message: str = ""
        self._recipient_username: str = ""
        self._sender_username: str = ""
        self._time: int = 0

# OBJECT MODEL

class BaseRequest(object):
    def __init__(self):
        pass

class BaseResponse(object):
    def __init__(self):
        self._error: Optional[str] = None

# Function 0: Log In Account

class LogInAccountRequest(BaseRequest):
    def __init__(self):
        self._username: str = ""

class LogInAccountResponse(BaseResponse):
    def __init__(self):
        pass

# Function 1: Create Account

class CreateAccountRequest(BaseRequest):
    def __init__(self):
        self._username: str = ""

class CreateAccountResponse(BaseResponse):
    def __init__(self):
        pass

# Function 2: List Accounts

class ListAccountsRequest(BaseRequest):
    def __init__(self):
        pass

class ListAccountsResponse(BaseResponse):
    def __init__(self):
        self._accounts: list[Account] = []

# Function 3: Send Message

class SendMessageRequest(BaseRequest):
    def __init__(self):
        self._message: str = ""
        self._recipient_username: str = ""
        self._sender_username: str = ""

class SendMessageResponse(BaseResponse):
    def __init__(self):
        pass

# Function 4: Deliver Undelivered Messages

class DeliverUndeliveredMessagesRequest(BaseRequest):
    def __init__(self):
        self._username: str = ""

class DeliverUndeliveredMessagesResponse(BaseResponse):
    def __init__(self):
        self._messages: list[Message] = []

# Function 5: Delete Account

class DeleteAccountRequest(BaseRequest):
    def __init__(self):
        self._username: str = ""

class DeleteAccountResponse(BaseResponse):
    def __init__(self):
        pass
