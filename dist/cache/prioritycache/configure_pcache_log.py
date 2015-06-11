#!/usr/bin/env python

import logging
import config_cnd
import sys


def configure_log_file(log_filename=config_cnd.LOG_FILENAME, log_level=logging.INFO):
    """ Module to configure the log file and the log parameters.
    Logs are streamed to the log file as well as the screen.
    """
    config_cnd.LOG = logging.getLogger(config_cnd.LOG_NAME)
    config_cnd.LOG_LEVEL = log_level
    config_cnd.LOG.setLevel(config_cnd.LOG_LEVEL)
    log_formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')

    # Add the handler to print to the screen
    handler1 = logging.StreamHandler(sys.stdout)
    handler1.setFormatter(log_formatter)
    config_cnd.LOG.addHandler(handler1)
    
    # Add the handler to for the file if present
    if log_filename:
        print("Configuring log file: {}".format(log_filename))
        handler2 = logging.FileHandler(filename=log_filename)
        handler2.setFormatter(log_formatter)
        config_cnd.LOG.addHandler(handler2)
        print("Started logging in the log file:{}".format(log_filename))


