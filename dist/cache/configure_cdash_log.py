#!/usr/bin/env python
""""
Cache-n-DASH: A Caching Framework for DASH video streaming.

Authors: Parikshit Juluri, Sheyda Kiyani Meher, Rohit Abhishek
Institution: University of Missouri-Kansas City
Contact Email: pjuluri@umkc.edu
"""

import logging
import config_cdash
import sys


def configure_cdash_log(log_filename=config_cdash.LOG_FILENAME, log_level=logging.INFO):
    """ Module to configure the log file and the log parameters.
    Logs are streamed to the log file as well as the screen.
    """
    config_cdash.LOG = logging.getLogger(config_cdash.LOG_NAME)
    config_cdash.LOG_LEVEL = log_level
    config_cdash.LOG.setLevel(config_cdash.LOG_LEVEL)
    log_formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')

    # Add the handler to print to the screen
    handler1 = logging.StreamHandler(sys.stdout)
    handler1.setFormatter(log_formatter)
    config_cdash.LOG.addHandler(handler1)
    
    # Add the handler to for the file if present
    if log_filename:
        print("Configuring log file: {}".format(log_filename))
        handler2 = logging.FileHandler(filename=log_filename)
        handler2.setFormatter(log_formatter)
        config_cdash.LOG.addHandler(handler2)
        print("Started logging in the log file:{}".format(log_filename))


