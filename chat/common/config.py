# config.py
# in chat.common

class Config:
    HOST = '10.250.234.111'  # "10.250.25.88"
    MAX_WORKERS = 10
    PORT = 8081
    TIMEOUT = 1
    STR_MAX_LEN = 280
    LIST_MAX_LEN = 255
    INT_MAX_LEN = 1 << 64
    POLL_TIME = 0.1
