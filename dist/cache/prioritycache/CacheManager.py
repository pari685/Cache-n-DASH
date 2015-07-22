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
import time
from prioritycache.cache_module import check_content_server
from prioritycache.cache_module import segment_exists
from prioritycache.prefetch_scheme import get_prefetch
from PriorityCache import PriorityCache
import config_cdash
import Queue


class CacheManager():
    def __init__(self, cache_size=config_cdash.CACHE_LIMIT):
        """ Initialize the Cache manager. 
            Start the Priority Cache with max_size = cache_size
        """
        self.fetch_requests = 0
        self.prefetch_request_count = 0
        config_cdash.LOG.info('Initializing the Cache Manager')
        self.cache = PriorityCache(cache_size)
        self.prefetch_queue = Queue.Queue()
        self.current_queue = Queue.Queue()
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
        local_filepath, http_headers = self.cache.get_file(file_path, config_cdash.FETCH_CODE)
        self.fetch_requests += 1
        config_cdash.LOG.info('Total fetch Requests = {}'.format(self.fetch_requests))
        return local_filepath, http_headers

    def current_function(self):
        """
        Thread reads the current requests and generates the prefetch requests
        that determines the next segment for all the current fetched bitrates.

        We use a separate prefetch queue to ensure that the prefetch does not affect the performance
        of the current requests
        """
        current_request = None
        while not self.stop.is_set():
            try:
                current_request = self.current_queue.get(timeout=None)
            except Queue.Empty:
                config_cdash.LOG.error('Current Thread: Thread GET returned Empty value')
                # time.sleep(config_cdash.WAIT_TIME)
                current_request = None
                continue
            # Determining the next bitrates and adding to the prefetch list
            if current_request:
                prefetch_request, prefetch_bitrate = get_prefetch(current_request, 'BASIC')
            if not segment_exists(prefetch_request):
                if check_content_server(prefetch_request):
                    config_cdash.LOG.info('Current Thread: Current segment: {}, Next segment: {}'.format(current_request,
                                                                                                  prefetch_request))
                    self.prefetch_queue.put(prefetch_request)
                else:
                    config_cdash.LOG.info('Current Thread: Invalid Next segment: {}'.format(current_request, prefetch_request))
        else:
            config_cdash.LOG.warning('Current Thread: terminated')

    def prefetch_function(self):
        """ Function that reads the contents of the prefetch table in the database and pre-fetches the file into
            the cache
            We use a separate prefetch queue to ensure that the prefetch does not affect the performance
            of the current requests
        """
        while not self.stop.is_set():
            try:
                # Pre-fetching the files
                prefetch_request = self.prefetch_queue.get(timeout=None)
            except Queue.Empty:
                config_cdash.LOG.error('Could not read from the Prefetch queue')
                time.sleep(config_cdash.WAIT_TIME)
                continue
            config_cdash.LOG.info('Pre-fetching the segment: {}'.format(prefetch_request))
            self.cache.get_file(prefetch_request, config_cdash.PREFETCH_CODE)
            self.prefetch_request_count += 1
            config_cdash.LOG.info('Total prefetch Requests = {}'.format(self.prefetch_requests))
        else:
            config_cdash.LOG.warning('Prefetch thread terminated')
