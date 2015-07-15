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
import threading
import sqlite3
import time
from prioritycache.cache_module import check_content_server
from prioritycache.cache_module import segment_exists
from prioritycache.prefetch_scheme import get_next_simple
from PriorityCache import PriorityCache
import config_cdash
from create_db import create_db



class CacheManager():
    def __init__(self, cache_size=config_cdash.CACHE_LIMIT):
        """ Initialize the Cache manager. 
            Start the Priority Cache with max_size = cache_size
        """
        self.fetch_requests = 0
        self.prefetch_requests = 0
        config_cdash.LOG.info('Initializing the Cache Manager')
        self.cache = PriorityCache(cache_size)
        self.conn = create_db(config_cdash.CACHE_DATABASE, config_cdash.TABLE_LIST)
        self.cur = self.conn.cursor()
        self.stop = threading.Event()
        self.current_thread = threading.Thread(target=self.current_function, args=())
        self.current_thread.daemon = True
        self.current_thread.start()
        config_cdash.LOG.info('Started the Current fetch thread')
        self.prefetch_thread = threading.Thread(target=self.prefetch_function, args=())
        self.prefetch_thread.daemon = True
        self.prefetch_thread.start()
        config_cdash.LOG.info('Started the Preftech thread')

    def terminate(self):
        self.stop.set()
        self.prefetch_thread.join()
        self.current_thread.join()

    def fetch_file(self, file_path):
        """ Module to get the file """
        config_cdash.LOG.info('Fetching the file {}'.format(file_path))
        # Add the current request to the current_thread
        # This is to ensure that the pre-fetch process does not hold the
        # FETCH process self.cur.execute("CREATE TABLE Current(ID INT, Segment Text)")
        self.cur.execute("INSERT INTO Current(Segment) VALUES('{}');".format(file_path))
        # Return the file path
        self.conn.commit()
        local_filepath, http_headers = self.cache.get_file(file_path, config_cdash.FETCH_CODE)
        self.fetch_requests += 1
        config_cdash.LOG.info('Total fetch Requests = {}'.format(self.fetch_requests))
        return local_filepath, http_headers

    def current_function(self):
        """
        Module that determines the next segment for all the current fetched bitrates
        """
        thread_conn = create_db(config_cdash.CACHE_DATABASE, config_cdash.TABLE_LIST)
        thread_cur = thread_conn.cursor()
        while not self.stop.is_set():
            try:
                thread_cur.execute('Select * from Current')
            except sqlite3.OperationalError:
                config_cdash.LOG.error('CTHREAD: Could not read from the Current table')
                time.sleep(config_cdash.WAIT_TIME)
                continue
            rows = thread_cur.fetchall()
            # Determining the next bitrates and adding to the prefetch list
            for row in rows:
                current_request = row[0]
                while True:
                    try:
                        thread_cur.execute("DELETE FROM Current WHERE Segment='{}';".format(current_request))
                        break
                    except sqlite3.OperationalError:
                        continue
                next_request = get_next_simple(current_request)
                if not segment_exists(next_request):
                    if check_content_server(next_request):
                        config_cdash.LOG.info('CTHREAD: Current segment: {}, Next segment: {}'.format(current_request, next_request))
                        thread_cur.execute("INSERT INTO Prefetch(Segment) VALUES('{}');".format(next_request))
                    else:
                        config_cdash.LOG.info('CTHREAD: Invalid Next segment: {}'.format(current_request, next_request))
                thread_conn.commit()
        else:
            config_cdash.LOG.warning('Current thread terminated')

    def prefetch_function(self):
        """ Function that reads the contents of the prefetch table in the database and pre-fetches the file into
            the cache
        """
        thread_conn = create_db(config_cdash.CACHE_DATABASE, config_cdash.TABLE_LIST)
        thread_cur = thread_conn.cursor()
        while not self.stop.is_set():
            try:
                # Pre-fetching the files
                # TODO: Extend the weightage parameter
                thread_cur.execute('SELECT * from Prefetch;')
            except sqlite3.OperationalError:
                config_cdash.LOG.error('Could not read from the Prefetch table')
                time.sleep(config_cdash.WAIT_TIME)
                continue
            rows = thread_cur.fetchall()
            for row in rows:
                prefetch_request = row[0]
                while True:
                    # Try to write to database.
                    try:
                        thread_cur.execute("DELETE FROM Prefetch WHERE Segment='{}';".format(prefetch_request))
                        break
                    except sqlite3.OperationalError:
                        continue
                thread_conn.commit()
                config_cdash.LOG.info('Pre-fetching the segment: {}'.format(prefetch_request))
                self.cache.get_file(prefetch_request, config_cdash.PREFETCH_CODE)
                self.prefetch_requests += 1
                config_cdash.LOG.info('Total prefetch Requests = {}'.format(self.prefetch_requests))
        else:
            config_cdash.LOG.warning('Prefetch thread terminated')