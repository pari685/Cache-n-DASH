#!/usr/bin/env python

import logging
import config_pcache
import sys


def configure_log_file(log_filename=config_pcache.LOG_FILENAME, log_level=logging.INFO):
    """ Module to configure the log file and the log parameters.
    Logs are streamed to the log file as well as the screen.
    """
    config_pcache.LOG = logging.getLogger(config_pcache.LOG_NAME)
    config_pcache.LOG_LEVEL = log_level
    config_pcache.LOG.setLevel(config_pcache.LOG_LEVEL)
    log_formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')

    # Add the handler to print to the screen
    handler1 = logging.StreamHandler(sys.stdout)
    handler1.setFormatter(log_formatter)
    config_pcache.LOG.addHandler(handler1)
    
    # Add the handler to for the file if present
    if log_filename:
        print("Configuring log file: {}".format(log_filename))
        handler2 = logging.FileHandler(filename=log_filename)
        handler2.setFormatter(log_formatter)
        config_pcache.LOG.addHandler(handler2)
        print("Started logging in the log file:{}".format(log_filename))


