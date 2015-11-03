__author__ = 'pjuluri'

from download_file import download_file
import collections
import glob
import os
import config_cdash


def download_segment(segment_path):
    """ Function to download the segment"""
    segment_url = config_cdash.CONTENT_SERVER + segment_path
    segment_filename = segment_path.replace('/', '-')
    local_filepath = os.path.join(config_cdash.VIDEO_FOLDER, segment_filename)
    return download_file(segment_url, local_filepath)


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
        # Creating a queue for the FIFO cache
        self.cache_queue = collections.deque()
        # Creating a dict for the weighted cache
        self.cache_dict = collections.defaultdict(int)
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

    def initialize_cache(self, local_folder=config_cdash.VIDEO_FOLDER):
        current_files = glob.glob(local_folder + '*.m4s')
        for current_file in current_files:
            try:
                os.remove(current_file)
            except IOError:
                config_cdash.LOG.error('Unable to delete the cache file {}. Skipping'.format(current_file))
                continue

    def get_file(self, key, code=config_cdash.FETCH_CODE):
        """ Get the file from the cache.
        If not get it from the content server
        """
        config_cdash.LOG.info("code = {}".format(code))
        # config_cdash.LOG.info('Current Cache Dict= {}'.format(self.cache.keys()))
        try:
            local_filepath, http_headers = self.cache[key]
            try:
                self.cache_dict[key] += 1
            except KeyError:
                self.cache_dict[key] = 1
            if code == config_cdash.FETCH_CODE:
                self.fetch_hits += 1
                config_cdash.LOG.info('Fetch hit count = {} Fetch hit: {}'.format(self.fetch_hits, key))
            elif code == config_cdash.PREFETCH_CODE:
                self.prefetch_hits += 1
                config_cdash.LOG.info('Prefetch hit count = {}. Prefetch hit: {}'.format(self.prefetch_hits, key))
        except KeyError:
            # The file is not in the cache.
            # Need to fetch from content server
            # TODO: Check if the request is valid (Use Rohit's code)
            if key not in self.cache:
                local_filepath, http_headers = download_segment(key)
                self.cache[key] = (local_filepath, http_headers)
                self.cache_queue.append(key)
                config_cdash.LOG.info('Adding key {} to cache'.format(key))
                if code == config_cdash.FETCH_CODE:
                    self.misses += 1
                    config_cdash.LOG.info('Cache miss: count = {},{}'.format(self.misses, key))
            else:
                local_filepath, http_headers = self.cache[key]
                config_cdash.LOG.info('key {} already in Cache'.format(key))
            while True:
                if len(self.cache) > self.maxsize:
                    self.pop_cache()
                else:
                    break
        return local_filepath, http_headers

    def pop_cache(self):
        """ Module to pop an item from the cache.
            Based on LRU
        """
        key = self.cache_queue.popleft()
        try:
            del self.cache[key]
            config_cdash.LOG.info('Deleted Key {} from Cache'.format(key))
        except KeyError:
            config_cdash.LOG.error('Key {} not found in Cache'.format(key))

    def pop_dict(self):
        """
        Module to remove an element from the dict
        :param self:
        :return:
        """
        lowest_value = min(self.cache_dict.values())
        for key in self.cache_dict:
            if self.cache_dict[key] == lowest_value:
                try:
                    del self.cache_dict[key]
                except KeyError:
                    config_cdash.LOG.error('Could not find key: {} in cache_dict'.format(key))
                try:
                    del self.cache[key]
                except KeyError:
                    config_cdash.LOG.error('Could not find key: {} in cache'.format(key))
                config_cdash.LOG.info('Deleting key {}'.format(key))
                break

    def clear(self):
            self.cache.clear()
            self.cache_queue.clear()
            self.refcount.clear()
            self.misses = self.fetch_hits = self.prefetch_hits = 0