#!/usr/bin/env python
""""
Cache-n-DASH: A Caching Framework for DASH video streaming.

Authors: Parikshit Juluri, Sheyda Kiyani Meher, Rohit Abhishek
Institution: University of Missouri-Kansas City
Contact Email: pjuluri@umkc.edu
"""

import urllib2
import timeit
import os
import config_cdash
import errno
import urlparse

DOWNLOAD_CHUNK = 1024

def make_sure_path_exists(folder_path):
    """ Module to make sure the path exists if not create the folder path
    """
    try:
        os.makedirs(folder_path)
        config_cdash.LOG.info('Created the cache folder {}'.format(folder_path))
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            config_cdash.LOG.error('Unable to create the cache folder {}'.format(folder_path))
            raise

def download_file(segment_url, segment_filepath):
    """ Module to download the segment """
    # Connecting to the content server
    try:
        connection = urllib2.urlopen(segment_url)
    except urllib2.HTTPError:
        config_cdash.LOG.error("Unable to connect to the content server. {}".format(segment_url))
        raise
    # Retrieving the content length
    content_length = connection.headers['content-length']
    http_headers = dict(connection.headers)
    parsed_uri = urlparse.urlparse(segment_url)
    segment_path = '{uri.path}'.format(uri=parsed_uri)
    while segment_path.startswith('/'):
        segment_path = segment_path[1:]
    make_sure_path_exists(os.path.dirname(segment_filepath))
    try:
        segment_file_handle = open(segment_filepath, 'wb')
    except IOError:
        config_cdash.LOG.error('Unable to open local file for writing: {}'.format(segment_filepath))
        return None
    segment_size = 0
    # Start the timer for download
    download_start_time = timeit.default_timer()
    # Downloading the segment form the content server in chunks of size DOWNLOAD_CHUNK
    while True:
        segment_data = connection.read(DOWNLOAD_CHUNK)
        segment_size += len(segment_data)
        segment_file_handle.write(segment_data)
        if len(segment_data) < DOWNLOAD_CHUNK:
            break
    connection.close()
    download_time = timeit.default_timer() - download_start_time
    segment_file_handle.close()
    config_cdash.LOG.info('Retrieved the segment {} of size \  '
                          '{} in time {} from the content server'.format(segment_url, segment_size, download_time))
    return segment_filepath, http_headers