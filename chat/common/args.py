# args.py
# in chat.common

import argparse


def make_parser():
    """Makes a parser for command line arguments (i.e. host and port).
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--id',
                        dest='machine_id',
                        required=False,
                        type=int,
                        default=0,
                        help='string saying this is the nth machine')
    return parser


def parse_client_args():
    """Parse the command line arguments (i.e. host and port and shiny).

        Returns: an `argparse.Namespace` (filtering out `None` values).
    """
    parser = make_parser()
    parser.add_argument('--shiny', action='store_true')
    return argparse.Namespace(**{k: v
                                 for k, v in
                                 parser.parse_args().__dict__.items()
                                 if v is not None})


def parse_server_args():
    """Parse the command line arguments (i.e. host and port).

        Returns: an `argparse.Namespace` (filtering out `None` values).
    """
    parser = make_parser()
    return argparse.Namespace(**{k: v
                                 for k, v in
                                 parser.parse_args().__dict__.items()
                                 if v is not None})
