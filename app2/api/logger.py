#!/usr/bin/env ipython
__version__ = "0.0.1"

import logging as lg
import logging.handlers as handlers
from os import path, makedirs
from subprocess import getoutput
from datetime import datetime
from toolz import memoize


@memoize
def get_project_dir():
    """Python makes it difficult to yeld our project root... not sure how this
    will work as a python site package; it won't work in service fabric where
    git might not be on the path. For testing only."""
    return path.abspath(getoutput("git rev-parse --show-toplevel"))


def __create_logger(log_level=lg.DEBUG):
    "Creates a logger, to be stored globally."

    root_logger = lg.getLogger(__name__)
    root_logger.setLevel(log_level)

    # Log formatter for streamhandler (console)
    log_formatter = lg.Formatter("%(asctime)s [%(levelname)-5.5s] %(module)s -> %(message)s")

    # For printing to tmux session console
    console_handler = lg.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # The filehandler will be added separately in the set_logger_file call
    return root_logger


# global on import
logger = __create_logger()


def set_logger_file(a_lg, log_file_dir, log_level=lg.DEBUG):
    """Adds a filehandler to our root logger, directing log writing to the
    provided directory. This will let us assign a different directory/log_file
    for each running module. TimedRotatingFileHandler rotates log files daily."""

    log_path = path.join(get_project_dir(), "logs", log_file_dir)
    if not path.exists(log_path):
        print('Creating the following directory for storing logs: ' + log_path)
        makedirs(log_path)

    file_name = log_file_dir + '.log'
    print(f'Setting up logger at {log_path}/{file_name}...')

    # FYI it uses local time for "midnight" unless you set utc=True
    file_handler = handlers.TimedRotatingFileHandler(f"{log_path}/{file_name}",
                                                     when="midnight",
                                                     interval=1,
                                                     backupCount=30)
    file_handler.suffix = "%Y%m%d"
    file_handler.setLevel(log_level)

    # Log formatter for filehandler
    log_formatter = lg.Formatter("%(asctime)s [%(levelname)-5.5s] %(module)s -> %(message)s")
    file_handler.setFormatter(log_formatter)
    a_lg.addHandler(file_handler)

    # Pretty sure I don't have to return it, changes are applied directly
    #return a_lg


set_logger_file(logger, "justlooks-api")
