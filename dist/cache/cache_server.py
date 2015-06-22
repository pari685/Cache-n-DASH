#!/usr/bin/env python

# for python 2.5
from __future__ import with_statement

import time
import BaseHTTPServer
import sys
import os
#import requests
import urllib2
import shutil
import read_mpd
import errno
import os.path
import socket
import hashlib
import json
import timeit
#import logging
import config_client
from configure_log_file import configure_log_file

sys.path.append('..')
#import pytomo
#from lib_youtube_download import get_data_duration

HOSTNAME = 'localhost'
PORT_NUMBER = 8001

MPD_SOURCE_DICT = {
	'BigBuckBunny/4sec/BigBuckBunny_4s_simple_2014_05_09.mpd':'http://www-itec.uni-klu.ac.at/ftp/datasets/DASHDataset2014/BigBuckBunny/4sec/BigBuckBunny_4s_simple_2014_05_09.mpd',
	'ElephantsDream/4sec/ElephantsDream_4s_simple_2014_05_09.mpd':'http://www-itec.uni-klu.ac.at/ftp/datasets/DASHDataset2014/ElephantsDream/4sec/ElephantsDream_4s_simple_2014_05_09.mpd'
}

MPD_LIST = {}

USER_DICT = {}

class MyHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    "HTTPHandler to serve the video"

    #check if MPD_LIST file in cache exists
    
    if os.path.exists('MPD_LIST.json') == True:
       #print 'I have these in cache!\n'
       with open('MPD_LIST.json', 'rb') as infile:
                MPD_LIST = json.load(infile)
       print MPD_LIST, "\n"

    def do_GET(self):

        "Function to handle the get message"
        request = self.path.strip("/").split('?')[0]

        #check if mpd file requested is in Cahce Server (dictionary)
        if request in MPD_LIST:

            valid_request = True
            with open(request, 'rb') as request_file:
                self.wfile.write(request_file.read())
                self.send_response( 200 )
                self.send_header('ContentType', 'text/plain;charset=utf-8')
                self.end_headers()
                print "read the mpd file from cache! And write it in Client\n"

	#if mpd not in cache server take it from content server
        else:

            valid_request = False
            print "mpd NOT here in Cache Server, I have to get it from Content Server!\n"

            print socket.gethostbyname(socket.gethostname()),"it is IP of machine\n"

            #if mpd is in content server save it in cache server and put it in MPD_LIST and json file
            if request in MPD_SOURCE_DICT:

                print "Heyyy MPD is in Content Server ;)\n"
                mpd_directory = MPD_SOURCE_DICT[request]
                print mpd_directory,"this is the path\n"
                #response = requests.get(mpd_directory,stream=True)
                response = urllib2.urlopen(mpd_directory)
                print request;"this is request that I got from content server\n"
		#make directory in cache for request
                make_path = os.path.dirname(request)

                make_sure_path_exists(os.path.dirname(request))
		
                MPD_NAME = os.path.basename(request)
		
                # Assumes the default UTF-8
                hash_object = hashlib.md5(MPD_NAME.encode())
                print(hash_object.hexdigest())
                print "I made hash of mpd file name just for fun :D\n"

                with open(request,'wb') as out_file:
                     #shutil.copyfileobj(response.raw, out_file)
                      shutil.copyfileobj(response, out_file)
                print "put in local cache server!\n"
                with open(request, 'rb') as request_file:
                        self.wfile.write(request_file.read())
                        self.send_response( 200 )
                        self.send_header('ContentType', 'text/plain;charset=utf-8')
                        self.end_headers()
                print "now read from the cache server!\n"

                configure_log_file()

                #parse mpd that you have in cache
                dash_playback_object = read_mpd.read_mpd(request)
                print "this is what I got after traversing the mpd file in cache:\n"	
                print dash_playback_object.video['bandwidth_list']	
                MPD_LIST[request] = dash_playback_object.video['bandwidth_list']

                print "\nResult! in the dictionary in the cache : ",MPD_LIST,"\n"

		#use json file in cache
                with open('MPD_LIST.json', 'wb') as outfile:
                       json.dump(MPD_LIST, outfile)
                print "put dictionary in json file in cache!\n"

                #read from json file from cache
                with open('MPD_LIST.json', 'rb') as infile:
                       print 'inside json file in cache : ',json.load(infile)
                print "read from json file! Content of dictionary\n"


                UserSessionID = (socket.gethostbyname(socket.gethostname()),PORT_NUMBER,request);
                USER_DICT[UserSessionID] = MPD_LIST
                print "Cache Result USER_Session!",USER_DICT

            else:
                self.send_response( 404 )
	 

def make_sure_path_exists(path):
    """ Module to make sure the path exists if not create it
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def main():

    #logging.basicConfig(filename='mylog.log',level=logging.INFO)
    #logging.info('Started')
    "Function to start server"
    http_server = BaseHTTPServer.HTTPServer((HOSTNAME, PORT_NUMBER),
                                            MyHTTPRequestHandler)
    print "Listening on ", PORT_NUMBER, " - press ctrl-c to stop"
    http_server.serve_forever()

if __name__ == "__main__":
    sys.exit(main())
