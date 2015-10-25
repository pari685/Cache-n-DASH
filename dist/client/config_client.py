#!/usr/bin/env python
#
#   Cache n DASH
#   Parikshit Juluri
#	Sheyda Kiyani Meher
#   Rohit Abhishek
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

from time import strftime
import os
import random
from string import digits, ascii_uppercase

# Legal characters for the session ID
LEGALS = digits + ascii_uppercase


def generate_session_id(length, char_set=LEGALS):
    """
    Module to generate a random string for the video session
    :param length: Length of the random string
    :param char_set: Characters that could be used
    :return: Random string
    """
    session_id = str()
    for _ in range(length):
        session_id += random.choice(char_set)
    return session_id


try:
    import socket
    USERNAME = socket.gethostname()
except:
    USERNAME = 'TESTING'

COOKIE_FIELDS = {'Session-ID': generate_session_id(6),
                 'Username': USERNAME}

# The configuration file for the AStream module
# create logger
LOG_NAME = 'Cache-n-DASH_log'
LOG_LEVEL = None
# Set '-' to print to screen
LOG_FOLDER = "LOGS/"
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

LOG_FILENAME = os.path.join(LOG_FOLDER, 'DASH_CLIENT_LOG')
# Logs related to the statistics for the video
# PLAYBACK_LOG_FILENAME = os.path.join(LOG_FOLDER, strftime('DASH_PLAYBACK_LOG_%Y-%m-%d.%H_%M_%S.csv'))
# Buffer logs created by dash_buffer.py
BUFFER_LOG_FILENAME = os.path.join(LOG_FOLDER, strftime('DASH_client_LOG_%Y-%m-%d.%H_%M_%S.csv'))
LOG_FILE_HANDLE = None
# To be set by configure_log_file.py
LOG = None
# JSON Filename
JSON_LOG = os.path.join(LOG_FOLDER, strftime('DASH_client_%Y-%m-%d.%H_%M_%S.json'))
JSON_HANDLE = dict()
JSON_HANDLE['playback_info'] = {'start_time': None,
                                'end_time': None,
                                'initial_buffering_duration': None,
                                'interruptions': {'count': 0, 'events': list(), 'total_duration': 0},
                                'up_shifts': 0,
                                'down_shifts': 0,
                                'available_bitrates':[]
                                }
# Throughput-Based Adaptation
# WARNING: MAKE SURE YOU CHANGE THESE IN THE CACHE AS WELL
# TODO: Set these paramters at the start. (MPD or cookies??)
BASIC_THRESHOLD = 10
BASIC_LOWER_THRESHOLD = 0.8
BASIC_UPPER_THRESHOLD = 1.1

# Number of segments for moving average
BASIC_DELTA_COUNT = 5
MAX_BUFFER_SIZE = 5
INITIAL_BUFFERING_COUNT = 2