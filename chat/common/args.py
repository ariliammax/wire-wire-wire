# args.py
# in chat.common

import argparse


def parse_args():
    """Parse the command line arguments (i.e. host and port).

        Returns: an `argparse.Namespace` (filtering out `None` values).
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, required=False)
    parser.add_argument('--port', type=str, required=False)
    return argparse.Namespace(**{k: v
                                 for k, v in
                                 parser.parse_args().__dict__.items()
                                 if v is not None})
