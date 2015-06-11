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

import collections
from Queue import PriorityQueue, Queue
from multiprocessing import Process
from download_file import download_file

FETCH_CODE = 'FETCH'
PREFETCH_CODE = 'PRE-FETCH'

CACHE_LIMIT = 100
PREFETCH_LIMIT = 100

class Counter(dict):
    '''Dictionary where the default value is 0'''
    def __missing__(self, key):
        return 0

class CacheManager():
    def __init__(self, cache_size=CACHE_LIMIT):
        """ Initialize the Cache manager. 
            Start the Priority Cache with max_size = cache_size """
        self.cache = PriorityCache(cache_size)
        self.prefetch_queue = PriorityQueue(maxsize=PREFETCH_LIMIT)
        # starting a new multiprocessing thread for prefetch
        self.current_queue = Queue()
        self.prefetch_process = Process(target=self.prefetch_function)
        self.current_process = Process(target=self.current_function)
        self.prefetch_process.start()
        self.prefetch_process.join()
        self.current_process.start()
        self.current_process.join()
        self.fetch_requests = 0
        self.prefetch_requests = 0

    def fetch_file(self, file_path):
        """ Module to get the file """
        # Add the current request to the current_thread
        # This is to ensure that the pre-fech process does not hold the
        # FETCH process
        self.current_queue.put(file_path)
        return self.cache.get_file(file_path, FETCH_CODE)

    def current_function(self):
        """
        :return:
        """
        current_request = self.prefetch_queue.get()
        # TODO: Determine the next bitrate
        next_bitrate = get_nextbitrate()
        self.prefetch(next_bitrate)

    def prefetch(self, file_path, priority_number=0):
        """ Module that assigns a file for prefetch. 
        Lower the priority number, higher is the priority"""
        self.prefetch_queue.put(priority_number, file_path)

    def prefetch_function(self):
        """ Process that checks the prefetch queue to frefetch the file"""
        file_path = self.prefetch_queue.get()
        self.cache.get_file(file_path, PREFETCH_CODE)

class PriorityCache():
    '''Least-recently-used cache decorator.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    Clear the cache with f.clear().
    http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used
    '''
    def __init__(self, maxsize):
        self.cache = {}
        # order that keys have been used
        self.cache_queue = collections.deque()
        self.maxsize = maxsize
        self.maxqueue = maxsize * 10
        self.use_count = Counter()
        # times each key is in the queue
        self.refcount = Counter()
        self.kwd_mark = object()
        self.misses = 0
        self.fetch_hits = 0
        self.prefetch_hits = 0

    def get_file(self, key, code):
        """ Get the file from the cache.
        If not get it from the content server """
        try:
            local_filepath_ = self.cache[key]
            if code == FETCH_CODE:
                self.fetch_hits += 1
            elif code == PREFETCH_CODE:
                self.prefetch_hits += 1
        except KeyError:
            # TODO: Check if the request is valid (Use Rohit's code)
            local_filepath = download_file(key)
            self.cache[key] = local_filepath, code
            if len(self.cache) > self.maxsize:
                self.pop_cache() 
            self.misses += 1
        return local_filepath

    def pop_cache(self):
        ''' Module to pop an item from the cache. 
            Based on LRU'''
        key = self.cache_queue_popleft()
        self.refcount[key] -= 1
        while self.refcount[key]:
            key = self.cache_queue_popleft()
            self.refcount[key] -= 1
        del self.cache[key], self.refcount[key]

    def clear(self):
            self.cache.clear()
            self.cache_queue.clear()
            self.refcount.clear()
            self.misses = self.fetch_hits = self.prefetch_hits = 0
