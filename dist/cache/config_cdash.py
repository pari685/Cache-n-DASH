#!/usr/bin/env python
""""
Cache-n-DASH: A Caching Framework for DASH video streaming.

Authors: Parikshit Juluri, Sheyda Kiyani Meher, Rohit Abhishek
Institution: University of Missouri-Kansas City
Contact Email: pjuluri@umkc.edu

    Copyright (C) 2015, Parikshit Juluri

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import os
import time
import logging
from time import strftime

# CACHE Server Parameters
HOSTNAME = 'localhost'
PORT_NUMBER = 8001
MPD_SOURCE_LIST = ['BigBuckBunny_4s_simple_2014_05_09.mpd']
CWD = os.getcwd()

MPD_DICT_JSON_FILE = os.path.join(CWD, 'MPD_DICT.json')
MPD_FOLDER = os.path.join(CWD, 'MPD_FILES')
if not os.path.exists(MPD_FOLDER):
    os.makedirs(MPD_FOLDER)
# Parameters for the priority cache
FETCH_CODE = 'FETCH'
PREFETCH_CODE = 'PRE-FETCH'
CONTENT_SERVER = 'http://www-itec.uni-klu.ac.at/ftp/datasets/DASHDataset2014/BigBuckBunny/4sec/'
VIDEO_FOLDER = os.path.join(CWD, 'Videos')
if not os.path.exists(VIDEO_FOLDER):
    os.makedirs(VIDEO_FOLDER)
else:
    print "Clearing the Cache"
    import glob
    video_match = os.path.join(VIDEO_FOLDER, "*")
    video_list = glob.glob(video_match)
    for video_file in video_list:
        os.remove(video_file)

CACHE_LIMIT = 100
PREFETCH_LIMIT = 100
PREFETCH_SCHEME = 'BASIC'
# PREFETCH_SCHEME = 'SMART'
CURRENT_THREAD = True
PREFETCH_THREAD = True

# The number of previous samples to be considered, If set as None then all samples are considered
# Throughput measurement limits
LIMIT = 5
# The throughput average scheme to be considered. Could be 'average' or 'harmonic_mean'
SCHEME = 'average'
TABLE_RETRY_TIME = 5

# We store the throughput values in a local database
THROUGHPUT_DATABASE_FOLDER = os.path.join(CWD, 'Throughput_db')
if not os.path.exists(THROUGHPUT_DATABASE_FOLDER):
    os.makedirs(THROUGHPUT_DATABASE_FOLDER)
THROUGHPUT_DATABASE = "throughput_{}.db".format(time.strftime("%Y-%m-%d_%H_%M_%S"))
THROUGHPUT_DATABASE = os.path.join(THROUGHPUT_DATABASE_FOLDER, THROUGHPUT_DATABASE)
THROUGHPUT_TABLES = ["CREATE TABLE THROUGHPUTDATA("
                     "ENTRYID TIMESTAMP, "
                     "USERNAME Text,"
                     "SESSIONID Text,"
                     "REQUESTID INTEGER PRIMARY KEY,"
                     "REQUESTSIZE FLOAT,"
                     "REQUESTTIME FLOAT,"
                     "THROUGHPUT FLOAT);"]

# Cache Logging
LOG_NAME = 'cache_LOG'
# LOG level to be set by the configure_log file
LOG_LEVEL = logging.INFO

# Initialize the Log Folders
LOG_FOLDER = os.path.join(CWD, "Cache_LOGS")
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)
LOG_FILENAME = os.path.join(LOG_FOLDER, strftime('cache_n_dash_LOG_{}_%Y-%m-%d.%H_%M_%S.log'.format(PREFETCH_SCHEME)))
LOG_FILE_HANDLE = None
# To be set by configure_log_file.py
LOG = None

# TODO: Maybe put the following in a JSON?
VIDEO_CACHE_CONTENT = {
    'bunny': {'available-bitrate': [45226, 88783, 128503, 177437, 217761, 255865, 323047, 378355, 509091,
                                    577751, 782553, 1008699, 1207152, 1473801, 2087347, 2409742, 2944291,
                                    3340509, 3613836, 3936261],
              'segment-range': [1, 150],
              'string-match': 'BigBuckBunny_4s'},
    'forest': {'available-bitrate': [46516, 91651, 136761, 185092, 231141, 276163, 365184, 461029, 552051,
                                     642534,824821, 1005167, 1260896, 1512020, 1754001, 2143443, 2506133,
                                     3170853, 3744774],
               'segment-range':[1, 114],
               'string-match': 'OfForestAndMen_4s'},
    'swiss': {'available-bitrate': [88745, 128171, 172453, 215003, 255984, 330491, 430406, 600840, 754258,
                                    930297, 1323244, 1716694, 1988387, 2708994, 3430035, 3817613, 4003428],
              'segment-range': [4,78,34,20],
              'string-match': 'TheSwissAccount_4s'},
    'valkaama': {'available-bitrate': [45679, 85914, 118584, 172627, 209596, 242301, 298523, 1861036, 2317655, 2755290,
                                       3522543, 4118338, 4561266, 432505, 505903, 574104, 811486, 983335, 1217742,
                                       1422377],
                 'segment-range': [1, 1162],
                 'string-match': 'Valkaama_4'},
    'ed': {'available-bitrate': [45791, 89889, 129426, 179119, 220743, 259179, 323473, 375852, 516656,
                                 582757, 792489, 1016017, 1197604, 1456380, 2087288, 2394379, 2908119,
                                 3339937, 3666428, 4066615],
           'segment-range': [1, 164],
           'string-match': 'ElephantsDream_4s'},
    'redbull': {'available-bitrate': [100733, 149211, 200933, 250302, 299039, 395090, 500459, 700159, 891912,
                                      1171990, 1498197, 1991890, 2465785, 2995811, 3992562, 4979124,
                                      5936225],
                'segment-range': [1, 10],
                'string-match': 'RedBull_4'},
    'tos': {'available-bitrate': [101, 65509, 129510, 191511, 253270, 504741, 807450, 1506971, 2416099,
                                  3004351, 4011653, 6025488, 10045361],
            'segment-range': [1, 184],
            'string-match': 'TearsOfSteel_4s_'}
}

# Throughput Based Adaptation
# WARNING: MAKE SURE YOU CHANGE THESE IN THE CLIENT AS WELL
# TODO: Set these parameters at the start. (MPD or cookies??)
BASIC_THRESHOLD = 10
BASIC_UPPER_THRESHOLD = 1.2
# Number of segments for moving average
BASIC_DELTA_COUNT = 5
MAX_BUFFER_SIZE = 60
INITIAL_BUFFERING_COUNT = 2
