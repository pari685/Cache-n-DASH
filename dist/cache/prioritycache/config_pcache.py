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
LOG_NAME = 'PCache_LOG'
# LOG level to be setby the configure_log file
LOG_LEVEL = None

# Initialize the Log Folders
LOG_FOLDER = "CND_PCache_LOGS/"
if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)
LOG_FILENAME = os.path.join(LOG_FOLDER, 
        strftime('PCache_Runtime_LOG_%Y-%m-%d.%H_%M_%S.log'))
LOG_FILE_HANDLE = None
# To be set by configure_log_file.py
LOG = None
