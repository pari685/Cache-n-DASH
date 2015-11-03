#!/usr/bin/env python
"""
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
import BaseHTTPServer
import sys
import os
import urllib2
import shutil
import read_mpd
import errno
import hashlib
import json
import config_cdash
import time
import timeit
import datetime
from os import stat
import threading
from prioritycache import CacheManager
import configure_cdash_log
from prioritycache.cache_module import check_content_server
import create_db

# Active state data structures
MPD_DICT = {}

USER_DICT_LOCK = threading.Lock()
USER_DICT = {}

TH_CONN = None
cache_manager = None
# HTTP CODES
HTTP_OK = 200
HTTP_NOT_FOUND = 404

class MyHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """HTTPHandler to serve the video"""
    # check if MPD_DICT file in cache exists
    def do_GET(self):
        """Function to handle the get message"""
        entry_id = username = session_id = request_id = "NULL"
        request_size = throughput = request_time = "NULL"
        try:
            username = self.headers['Username']
            session_id = self.headers['Session-ID']
        except KeyError:
            config_cdash.LOG.warning('Could not find the username or session-ID for request from host:{}'.format(
                self.client_address))

        global MPD_DICT
        request = self.path.strip("/").split('?')[0]
        # check if mpd file requested is in Cache Server (dictionary)
        if request in MPD_DICT:
            config_cdash.LOG.info('Found MPD in MPD_DICT')
            request_path = request.replace('/', os.path.sep)
            make_sure_path_exists(config_cdash.MPD_FOLDER)
            local_mpd_path = os.path.join(config_cdash.MPD_FOLDER, request_path)
            for header in self.headers:
                config_cdash.LOG.info(header)
            self.send_response(HTTP_OK)
            for header, header_value in MPD_DICT[request]['http_headers'].items():
                self.send_header(header, header_value)
            self.end_headers()

            with open(local_mpd_path, 'rb') as request_file:
                start_time = timeit.default_timer()
                self.wfile.write(request_file.read())
                # Elapsed time in seconds
                request_time = timeit.default_timer() - start_time
                config_cdash.LOG.info('Served the MPD file from the cache server')
            request_size = stat(local_mpd_path).st_size

        elif request in config_cdash.MPD_SOURCE_LIST:
            config_cdash.LOG.info("MPD: not in cache. Retrieving from Content server".format(request))
            # if mpd is in content server save it in cache server and put it in MPD_DICT and json file
            mpd_headers = None
            mpd_url = config_cdash.CONTENT_SERVER + request
            try:
                content_server_response = urllib2.urlopen(mpd_url)
                mpd_headers = content_server_response.headers
                config_cdash.LOG.info('Fetching MPD from {}'.format(mpd_url))
            except urllib2.HTTPError as http_error:
                config_cdash.LOG.error('Unable to fetch MPD file from the content server url {}. HTTPError: {}'.format(
                    mpd_url, http_error.code))
            request_path = request.replace('/', os.path.sep)
            local_mpd_path = os.path.join(config_cdash.MPD_FOLDER, request_path)
            make_sure_path_exists(os.path.dirname(local_mpd_path))
            with open(local_mpd_path, 'wb') as local_mpd_file:
                shutil.copyfileobj(content_server_response, local_mpd_file)
            config_cdash.LOG.info('Downloaded the MPD: {} to {}'.format(content_server_response, local_mpd_path))
            self.send_response(HTTP_OK)
            for header, header_value in mpd_headers.items():
                self.send_header(header, header_value)
            self.end_headers()

            with open(local_mpd_path, 'rb') as request_file:
                start_time = timeit.default_timer()
                self.wfile.write(request_file.read())
                # Elapsed time in seconds
                request_time = timeit.default_timer() - start_time
            # file_size in bytes
            request_size = stat(local_mpd_path).st_size
            config_cdash.LOG.info('Served MPD file:{}'.format(local_mpd_path))
            # client_ip, client_port = self.client_address
            mpd_headers_dict = dict(mpd_headers)
            config_cdash.LOG.info('Parsing MPD file')
            parse_mpd(local_mpd_path, request, mpd_headers_dict, (username, session_id ))
        elif 'm4s' in request:
            # Check if it is a valid request
            config_cdash.LOG.info('Request for m4s {}'.format(request))
            if check_content_server(request):
                local_file_path, http_headers = cache_manager.fetch_file(request, username, session_id)
                config_cdash.LOG.debug('M4S request: local {}, http_headers: {}'.format(local_file_path, http_headers))
                self.send_response(HTTP_OK)
                for header, header_value in http_headers.items():
                    self.send_header(header, header_value)
                self.end_headers()
                with open(local_file_path, 'rb') as request_file:
                    start_time = timeit.default_timer()
                    self.wfile.write(request_file.read())
                    request_time = timeit.default_timer() - start_time
                request_size = stat(local_file_path).st_size

            else:
                config_cdash.LOG.warning('Invalid video file request: {}'.format(request))
        else:
            self.send_response(HTTP_NOT_FOUND)
            config_cdash.LOG.warning('Could not find file {}'.format(request))
            return
        # If valid request sent
        entry_id = datetime.datetime.now()
        cursor = TH_CONN.cursor()
        throughput = float(request_size)/request_time
        config_cdash.LOG.info('Adding row to Throughput database : '
                              'INSERT INTO THROUGHPUTDATA VALUES ({}, {}, {}, {}, {}, {}, {});'.format(
            entry_id, username, session_id, request_id, request_size, request_time, throughput))
        cursor.execute('INSERT INTO THROUGHPUTDATA(ENTRYID, USERNAME, SESSIONID, REQUESTSIZE, REQUESTTIME, THROUGHPUT) '
                       'VALUES (?, ?, ?, ?, ?, ?);', (entry_id, username, session_id, request_size, request_time,
                                                      throughput))
        TH_CONN.commit()


def parse_mpd(mpd_file, request, mpd_headers, client_id):
    """ Module to parse the MPD_file and update the global dictionaries MPD_DICT, USER_DICT
    :param mpd_file: Path to mpd_file on local machine
    :param request: HTTP request path string
    :param mpd_headers: HPP Headers
    :param client_address: (ip_address, port) of the user
    :return:
    """
    #parse mpd that you have in cache
    global USER_DICT, MPD_DICT, USER_DICT_LOCK
    dash_playback_object = read_mpd.read_mpd(mpd_file)
    MPD_DICT[request] = {'bandwidth_list': dash_playback_object.video['bandwidth_list'],
                         'http_headers': mpd_headers}
    # use json file in cache
    config_cdash.LOG.info('Added info of {}: {} to MPD_DICT'.format(request, MPD_DICT))
    with open(config_cdash.MPD_DICT_JSON_FILE, 'wb') as outfile:
        json.dump(MPD_DICT, outfile)
    with USER_DICT_LOCK:
        USER_DICT[client_id] = {'bitrates': dash_playback_object.video['bandwidth_list'],
                                'created': time.time()}
        config_cdash.LOG.info('Updated the USER_DICT with {} and bitrates {}'.format(
            client_id, dash_playback_object.video['bandwidth_list']))


def hash_code(file_name):
    """
    :param file_name:
    :return:
    """
    return hashlib.md5(file_name.encode())


def make_sure_path_exists(path):
    """ Module to make sure the path exists if not create it
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def main():
    """ Main program wrapper """

    config_cdash.LOG = configure_cdash_log.configure_log(config_cdash.LOG_FILENAME, config_cdash.LOG_NAME,
                                                         config_cdash.LOG_LEVEL)
    global MPD_DICT
    global TH_CONN
    global cursor
    config_cdash.LOG.info('Starting the cache in {} mode'.format(config_cdash.PREFETCH_SCHEME))
    if TH_CONN == None:
        TH_CONN = create_db.create_db(config_cdash.THROUGHPUT_DATABASE, config_cdash.THROUGHPUT_TABLES)
    try:
        with open(config_cdash.MPD_DICT_JSON_FILE, 'rb') as infile:
            MPD_DICT = json.load(infile)
    except IOError:
        config_cdash.LOG.warning('Starting Cache for first time. Could not find any MPD_json file. ')
    # Starting the Cache Manager
    global cache_manager
    config_cdash.LOG.info('Starting the Cache Manager')
    cache_manager = CacheManager.CacheManager()
    # Function to start server
    http_server = BaseHTTPServer.HTTPServer((config_cdash.HOSTNAME, config_cdash.PORT_NUMBER),
                                            MyHTTPRequestHandler)
    config_cdash.LOG.info("Cache-Server listening on {}, port:{} - press ctrl-c to stop".format(config_cdash.HOSTNAME,
                                                                                            config_cdash.PORT_NUMBER))
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        config_cdash.LOG.info('Terminating the Cache Manager')
        cache_manager.terminate()
        return

if __name__ == "__main__":
    sys.exit(main())