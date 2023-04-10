# config.py
# in chat.common

# Useful configuration constants throughout the codebase.
class Config:
    ADDRESSES = [
        ("127.0.0.1", 10310), # port should be a multiple of 10
        ("127.0.0.1", 20310), # port should be a multiple of 10
        ("127.0.0.1", 30310), # port should be a multiple of 10
    ]
    MAX_WORKERS = 10
    TIMEOUT_SYNC = 0.001
    TIMEOUT_QUEUE = 0.01
    TIMEOUT_CLIENT = 0.1
    STR_MAX_LEN = 280
    LIST_MAX_LEN = 255
    INT_MAX_LEN = 1 << 64
    POLL_TIME = 0.1
