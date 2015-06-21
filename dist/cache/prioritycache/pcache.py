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

Usage
=====

import pcache
cache_manager = CacheManager(CACHE_SIZE)
segment_path = CacheManager.fetch_file(segment_request)
"""

import collections
from multiprocessing import Process, Manager
import multiprocessing
import threading
import sqlite3
import time
from download_file import download_file
from simple_scheme import get_next_bitrate
import os
import logging
logger = multiprocessing.log_to_stderr(logging.INFO)

FETCH_CODE = 'FETCH'
PREFETCH_CODE = 'PRE-FETCH'
CONTENT_SERVER = 'http://www-itec.uni-klu.ac.at/ftp/datasets/DASHDataset2014'
LOCAL_FOLDER = 'C:\\Users\\pjuluri\\Desktop\\Videos\\'
CACHE_LIMIT = 100
PREFETCH_LIMIT = 100
CACHE_DATABASE = 'C:\\Users\\pjuluri\\Desktop\\Cache_db.db'

TABLE_LIST = ["CREATE TABLE Prefetch(Segment Text, Weightage INT)",
                  "CREATE TABLE Current(Segment Text)"]


cache_queue = collections.deque()
cache_queue_append, cache_queue_popleft = cache_queue.append, cache_queue.popleft
cache_queue_appendleft, cache_queue_pop = cache_queue.appendleft, cache_queue.pop


def download_segment(segment_path):
    """ Function to download the segment"""
    segment_url = CONTENT_SERVER + segment_path
    dir_name = os.path.dirname(segment_path)
    destination_folder = os.path.join(LOCAL_FOLDER)
    return download_file(segment_url, destination_folder)


class Counter(dict):
    """Dictionary where the default value is 0"""
    def __missing__(self, key):
        return 0

def create_db(database_name):
    """
    :param database_name:
    :return:
    """
    conn = sqlite3.connect(database_name)
    cur = conn.cursor()
    for table in TABLE_LIST:
        try:
            cur.execute(table)
        except sqlite3.OperationalError:
            print 'Table {} already exists. Skipping'.format(table)
    return conn

class CacheManager():
    def __init__(self, cache_size=CACHE_LIMIT):
        """ Initialize the Cache manager. 
            Start the Priority Cache with max_size = cache_size """
        self.cache = PriorityCache(cache_size)
        self.conn = create_db(CACHE_DATABASE)
        self.cur = self.conn.cursor()
        self.current_process = threading.Thread(target=self.pool_function, args=())
        self.current_process.daemon = True
        self.current_process.start()
        #self.current_process.join()
        self.fetch_requests = 0
        self.prefetch_requests = 0

    def terminate(self):
        """ Function to terminate all the processes"""
        self.current_process.terminate()
        self.prefetch_process.terminate()

    def fetch_file(self, file_path):
        """ Module to get the file """
        print 'Fetching the file {}'.format(file_path)
        # Add the current request to the current_thread
        # This is to ensure that the pre-fetch process does not hold the
        # FETCH process self.cur.execute("CREATE TABLE Current(ID INT, Segment Text)")
        self.cur.execute("INSERT INTO Current(Segment) VALUES('{}');".format(file_path))
        print "INSERT INTO Current(Segment) VALUES('{}');".format(file_path)
        # Return the file path
        self.conn.commit()
        print self.cache.cache
        return self.cache.get_file(file_path, FETCH_CODE)

    def pool_function(self):
        """
        :return:
        """
        thread_conn = create_db(CACHE_DATABASE)
        thread_cur = thread_conn.cursor()
        while True:
            try:
                thread_cur.execute('Select * from Current')
            except sqlite3.OperationalError:
                continue
            rows = thread_cur.fetchall()
            # Determining the next bitrates and adding to the prefetch list
            for row in rows:
                time.sleep(5)
                current_request = row[0]
                print current_request
                thread_cur.execute("DELETE FROM Current WHERE Segment='{}';".format(current_request))

                next_request = get_next_bitrate(current_request)
                # TODO: Check if file exists in cache before pre-fetching
                thread_cur.execute("INSERT INTO Prefetch(Segment) VALUES('{}');".format(next_request))
                thread_conn.commit()

            # Pre-fetching the files TODO: Extend the weightage parameter
            thread_cur.execute('SELECT * from Prefetch;')
            rows = thread_cur.fetchall()
            for row in rows:
                time.sleep(5)
                prefetch_request = row[0]
                thread_cur.execute("DELETE FROM Prefetch WHERE Segment='{}';".format(prefetch_request))
                self.cache.get_file(prefetch_request, PREFETCH_CODE)
                thread_conn.commit()

    def prefetch(self, file_path):
        """ Module that assigns a file for prefetch. 
        Lower the priority number, higher is the priority
        self.cur.execute("CREATE TABLE Prefetch(ID INT, Segment Text, Weightage INT)")
        """

    def prefetch_function(self):
        """ Process that checks the prefetch queue to prefetch the file"""
        while True:
            self.cur.execute('Select * from Prefetch')
            rows = self.cur.fetchall()
            for row in rows:
                time.sleep(5)
                prefetch_request = row[0]
                self.cur.execute('DELETE FROM Current WHERE Segment={};'.format(prefetch_request))
                self.cache.get_file(prefetch_request, PREFETCH_CODE)


class PriorityCache():
    """Least-recently-used cache decorator.
    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    Clear the cache with f.clear().
    http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used
    """
    def __init__(self, maxsize):
        self.cache = {}
        # order that keys have been used
        self.maxsize = maxsize
        self.maxqueue = maxsize * 10
        self.use_count = Counter()
        # times each key is in the queue
        self.refcount = Counter()
        self.kwd_mark = object()
        self.misses = 0
        self.fetch_hits = 0
        self.prefetch_hits = 0


    def get_file(self, key, code=FETCH_CODE):
        """ Get the file from the cache.
        If not get it from the content server """
        try:
            local_filepath = self.cache[key]
            if code == FETCH_CODE:
                self.fetch_hits += 1
            elif code == PREFETCH_CODE:
                self.prefetch_hits += 1
        except KeyError:
            # The file is not in the cache.
            # Need to fetch from content server
            # TODO: Check if the request is valid (Use Rohit's code)
            local_filepath = download_segment(key)
            self.cache[key] = local_filepath
            if len(self.cache) > self.maxsize:
                self.pop_cache() 
            self.misses += 1
        print self.cache
        return local_filepath

    def pop_cache(self):
        """ Module to pop an item from the cache.
            Based on LRU
        """
        key = cache_queue_popleft()
        self.refcount[key] -= 1
        while self.refcount[key]:
            key = cache_queue_popleft()
            self.refcount[key] -= 1
        del self.cache[key], self.refcount[key]

    def clear(self):
            self.cache.clear()
            cache_queue.clear()
            self.refcount.clear()
            self.misses = self.fetch_hits = self.prefetch_hits = 0


