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
from time import strftime

# CACHE Server Parameters
HOSTNAME = 'localhost'
PORT_NUMBER = 8001
MPD_SOURCE_LIST = ['BigBuckBunny/4sec/BigBuckBunny_4s_simple_2014_05_09.mpd',
                   'ElephantsDream/4sec/ElephantsDream_4s_simple_2014_05_09.mpd'
                   ]
MPD_DICT_JSON_FILE = 'C:\\Users\\pjuluri\\Desktop\\Videos\\MPD_DICT.json'
MPD_FOLDER = 'C:\\Users\\pjuluri\\Desktop\\MPD\\'
#####  Parameters for the priority cache
FETCH_CODE = 'FETCH'
PREFETCH_CODE = 'PRE-FETCH'
CONTENT_SERVER = 'http://www-itec.uni-klu.ac.at/ftp/datasets/DASHDataset2014/'
LOCAL_FOLDER = 'C:\\Users\\pjuluri\\Desktop\\Videos\\'
CACHE_LIMIT = 100
PREFETCH_LIMIT = 100
CURRENT_THREAD = True
PREFETCH_THREAD = True

CACHE_DATABASE = 'C:\\Users\\pjuluri\\Desktop\\Cache_db.db'
TABLE_RETRY_TIME = 5

TABLE_LIST = ["CREATE TABLE Prefetch(Segment Text, Weightage INT)",
              "CREATE TABLE Current(Segment Text)"]


# Cache Logging
LOG_NAME = 'cache_LOG'
# LOG level to be setby the configure_log file
LOG_LEVEL = None

# Initialize the Log Folders
LOG_FOLDER = "C:\\Users\\pjuluri\\Desktop\\Cache_LOGS\\"
if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)
LOG_FILENAME = os.path.join(LOG_FOLDER,
        strftime('cache_Runtime_LOG_%Y-%m-%d.%H_%M_%S.log'))

LOG_FILE_HANDLE = None
# To be set by configure_log_file.py
LOG = None
