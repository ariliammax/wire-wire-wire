# config.py
# in chat.common

# Useful configuration constants throughout the codebase.
class Config:
    ADDRESSES = [
        ("10.250.140.244", 40130), # port should be a multiple of 10
        ("10.250.78.122", 40130), # port should be a multiple of 10
        ("10.250.150.158", 40130), # port should be a multiple of 10
    ]
    MAX_WORKERS = 10
    TIMEOUT_SYNC = 0.1
    TIMEOUT_QUEUE = 1
    TIMEOUT_CLIENT = 10
    STR_MAX_LEN = 280
    LIST_MAX_LEN = 255
    INT_MAX_LEN = 1 << 64
    POLL_TIME = 0.1
