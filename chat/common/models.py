# models.py
# in chat.common

from chat.common.util import Model


# DATA MODELS


Account = Model.model_with_fields(logged_in=bool,
                                  username=str)


Message = Model.model_with_fields(delivered=bool,
                                  message=str,
                                  recipient_username=str,
                                  sender_username=str,
                                  time=int)


# OBJECT MODELS

# these are the basic ones.
BaseRequest = Model.model_with_fields()
BaseResponse = Model.model_with_fields(error=str)


# Function 0: Log In Account
LogInAccountRequest = BaseRequest.add_fields(username=str)
LogInAccountResponse = BaseResponse.add_fields()

# Function 1: Create Account
CreateAccountRequest = BaseRequest.add_fields(username=str)
CreateAccountResponse = BaseResponse.add_fields()


# Function 2: List Accounts
ListAccountsRequest = BaseRequest.add_fields()
ListAccountsResponse = BaseResponse.add_fields(accounts=list)


# Function 3: Send Message
SendMessageRequest = BaseRequest.add_fields(message=str,
                                            recipient_username=str,
                                            sender_username=str)
SendMessageResponse = BaseResponse.add_fields()


# Function 4: Deliver Undelivered Messages
DeliverUndeliveredMessagesRequest = BaseRequest.add_fields(username=str)
DeliverUndeliveredMessagesResponse = BaseResponse.add_fields(messages=list)


# Function 5: Delete Account
DeleteAccountRequest = BaseRequest.add_fields()
DeleteAccountResponse = BaseResponse.add_fields()
