# models.py
# in chat.common

from chat.common.util import model_from_fields


# DATA MODELS


Account = model_from_fields(logged_in=bool,
                            username=str)


Message = model_from_fields(delivered=bool,
                            message=str,
                            recipient_username=str,
                            sender_username=str,
                            time=int)


# OBJECT MODEL... TODO: add "inheritence" in chat.common.util.model_from_
BaseRequest = model_from_fields()
BaseResponse = model_from_fields(error=str)


# Function 0: Log In Account
LogInAccountRequest = model_from_fields(username=str)
LogInAccountResponse = model_from_fields()

# Function 1: Create Account
CreateAccountRequest = model_from_fields(username=str)
CreateAccountResponse = model_from_fields()


# Function 2: List Accounts
ListAccountsRequest = model_from_fields()
ListAccountsResponse = model_from_fields(accounts=list)


# Function 3: Send Message
SendMessageRequest = model_from_fields(message=str,
                                       recipient_username=str,
                                       sender_username=str)
SendMessageResponse = model_from_fields()


# Function 4: Deliver Undelivered Messages
DeliverUndeliveredMessagesRequest = model_from_fields(username=str)
DeliverUndeliveredMessagesResponse = model_from_fields(messages=list)


# Function 5: Delete Account
DeleteAccountRequest = model_from_fields()
DeleteAccountResponse = model_from_fields()
