__author__ = 'pjuluri'

from download_file import download_file
import collections
import glob
import os
import config_cdash

def download_segment(segment_path):
    """ Function to download the segment"""
    segment_url = config_cdash.CONTENT_SERVER + segment_path
    dir_name = os.path.dirname(segment_path)
    destination_folder = os.path.join(config_cdash.LOCAL_FOLDER)
    return download_file(segment_url, destination_folder)

class Counter(dict):
    """Dictionary where the default value is 0"""
    def __missing__(self, key):
        return 0

class PriorityCache():
    """Least-recently-used cache decorator.
    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    Clear the cache with f.clear().
    http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used
    """
    def __init__(self, maxsize):
        self.cache = {}
        cache_queue = collections.deque()
        cache_queue_append, cache_queue_popleft = cache_queue.append, cache_queue.popleft
        cache_queue_appendleft, cache_queue_pop = cache_queue.appendleft, cache_queue.pop
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
        self.initialize_cache()

    def initialize_cache(self, local_folder=config_cdash.LOCAL_FOLDER):
        current_files = glob.glob(local_folder + '*')
        for current_file in current_files:
            self.cache[os.path.basename(current_file)] = current_file
        print 'Initializing Cache to', self.cache

    def get_file(self, key, code=config_cdash.FETCH_CODE):
        """ Get the file from the cache.
        If not get it from the content server """
        try:
            local_filepath = self.cache[key]
            if code == config_cdash.FETCH_CODE:
                self.fetch_hits += 1
            elif code == config_cdash.PREFETCH_CODE:
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
