#!/usr/local/bin/python
"""
Author:            Parikshit Juluri
Contact:           pjuluri@umkc.edu
Testing:
    import dash_client
    mpd_file = <MPD_FILE>
    dash_client.playback_duration(mpd_file, 'http://198.248.242.16:8005/')

    From commandline:
    python dash_client.py -m "http://127.0.0.1:8001/BigBuckBunny_4s_simple_2014_05_09.mpd" -p "basic"

"""
from __future__ import division
import read_mpd
import urlparse
import urllib2
import random
import os
import sys
import errno
import timeit
import httplib
from string import ascii_letters, digits
from argparse import ArgumentParser
import basic_dash
import config_client
import dash_buffer
from configure_log_file import configure_log_file, write_json
import time
try:
    WindowsError
except NameError:
    from shutil import WindowsError

# Constants
DEFAULT_PLAYBACK = 'BASIC'
DOWNLOAD_CHUNK = 1024

# Globals for arg parser with the default values
# Not sure if this is the correct way ....
MPD = None
LIST = False
PLAYBACK = DEFAULT_PLAYBACK
DOWNLOAD = False
SEGMENT_LIMIT = None

class DashPlayback:
    """
    Audio[bandwidth] : {duration, url_list}
    Video[bandwidth] : {duration, url_list}
    """
    def __init__(self):
        self.min_buffer_time = None
        self.playback_duration = None
        self.audio = dict()
        self.video = dict()


def get_mpd(url, mpd_opener):
    """ Module to download the MPD from the URL and save it to file"""
    try:
        connection = mpd_opener.open(url, timeout=10)
    except urllib2.HTTPError, error:
        config_client.LOG.error("Unable to download MPD file HTTP Error: %s" % error.code)
        return None
    except urllib2.URLError:
        error_message = "URLError. Unable to reach Server.Check if Server active"
        config_client.LOG.error(error_message)
        return None
    except IOError, httplib.HTTPException:
        message = "Unable to , file_identifierdownload MPD file HTTP Error."
        config_client.LOG.error(message)
        return None
    
    mpd_data = connection.read()
    connection.close()
    mpd_file = url.split('/')[-1]
    mpd_file_handle = open(mpd_file, 'w')
    mpd_file_handle.write(mpd_data)
    mpd_file_handle.close()
    config_client.LOG.info("Downloaded the MPD file {}".format(mpd_file))
    return mpd_file


def get_bandwidth(data, duration):
    """ Module to determine the bandwidth for a segment download"""
    return data * 8/duration


def get_domain_name(url):
    """ Module to obtain the domain name from the URL
        From : http://stackoverflow.com/questions/9626535/get-domain-name-from-url
    """
    parsed_uri = urlparse.urlparse(url)
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    return domain


def id_generator(id_size=6):
    """ Module to create a random string with uppercase 
        and digits.
    """
    return 'TEMP_' + ''.join(random.choice(ascii_letters+digits) for _ in range(id_size))


def download_segment(segment_url, dash_folder):
    """ Module to download the segment """
    try:
        segment_opener = get_opener()
        connection = segment_opener.open(segment_url)
    except urllib2.HTTPError, error:
        config_client.LOG.error("Unable to download DASH Segment {} HTTP Error:{} ".format(
            segment_url, str(error.code)))
        return None
    parsed_uri = urlparse.urlparse(segment_url)
    segment_path = '{uri.path}'.format(uri=parsed_uri)
    while segment_path.startswith('/'):
        segment_path = segment_path[1:]        
    segment_filename = os.path.join(dash_folder, os.path.basename(segment_path))
    make_sure_path_exists(os.path.dirname(segment_filename))
    segment_file_handle = open(segment_filename, 'wb')
    segment_size = 0
    while True:
        segment_data = connection.read(DOWNLOAD_CHUNK)
        segment_size += len(segment_data)
        segment_file_handle.write(segment_data)
        if len(segment_data) < DOWNLOAD_CHUNK:
            break
    connection.close()
    segment_file_handle.close()
    return segment_size, segment_filename


def get_media_all(domain, media_info, file_identifier, done_queue):
    """ Download the media from the list of URL's in media
    """
    bandwidth, media_dict = media_info
    media = media_dict[bandwidth]
    media_start_time = timeit.default_timer()
    for segment in [media.initialization] + media.url_list:
        start_time = timeit.default_timer()
        segment_url = urlparse.urljoin(domain, segment)
        _, segment_file = download_segment(segment_url, file_identifier)
        elapsed = timeit.default_timer() - start_time
        if segment_file:
            done_queue.put((bandwidth, segment_url, elapsed))
    media_download_time = timeit.default_timer() - media_start_time
    done_queue.put((bandwidth, 'STOP', media_download_time))
    return None


def make_sure_path_exists(path):
    """ Module to make sure the path exists if not create it """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def print_representations(dp_object):
    """ Module to print the representations"""
    print "The DASH media has the following video representations/bitrates"
    for bandwidth in dp_object.video:
        print bandwidth


def start_playback(dp_object, domain, playback_type=None, download=False):
    """ Module that downloads the MPD-FIle and download
        all the representations of the Module to download
        the MPEG-DASH media.
        Example: start_playback_smart(dp_object, domain, "SMART", DOWNLOAD, video_segment_duration)

        :param dp_object:       The DASH-playback object
        :param domain:          The domain name of the server (The segment URLS are domain + relative_address)
        :param playback_type:   The type of playback
                                1. 'BASIC' - The basic adaptation scheme (Based on Throughput)
        :param download: Set to True if the segments are to be stored locally (Boolean). Default False
        :return:
    """
    # Initialize the DASH buffer
    video_segment_duration = dp_object.video['duration']/dp_object.video['timescale']	
    dash_player = dash_buffer.DashPlayer(dp_object.playback_duration, video_segment_duration)
    dash_player.start()
    # A folder to save the segments in
    file_identifier = id_generator()
    config_client.LOG.info("The segments are stored in %s" % file_identifier)
    # dp_list = defaultdict(defaultdict)
    bitrates = dp_object.video['bandwidth_list']
    bitrates.sort()
    average_dwn_time = 0
    segment_files = []
    # For basic adaptation
    previous_segment_times = []
    recent_download_sizes = []
    current_bitrate = bitrates[0]
    previous_bitrate = None
    total_downloaded = 0
    # Delay in terms of the number of segments
    delay = 0
    segment_duration = 0
    segment_download_time = None
    # Start playback of all the segments
    downloaded_duration = 0
    # for segment_number, segment in enumerate(dp_list, int(dp_object.video['start'])):
    segment_number = dp_object.video['start']
    while downloaded_duration < dp_object.playback_duration:
        config_client.LOG.info(" {}: Processing the segment {}".format(playback_type.upper(), segment_number))
        try:
            write_json()
        except IOError:
            config_client.LOG.error('Unable to write to JSON {} to file'.format(config_client.JSON_HANDLE))

        if not previous_bitrate:
            previous_bitrate = current_bitrate
        if SEGMENT_LIMIT:
            if not dash_player.segment_limit:
                dash_player.segment_limit = int(SEGMENT_LIMIT)
            if segment_number > int(SEGMENT_LIMIT):
                config_client.LOG.info("Segment limit reached")
                break
        if segment_number == dp_object.video['start']:
            current_bitrate = bitrates[0]
        else:
            if playback_type.upper() == "BASIC":
                current_bitrate, average_dwn_time = basic_dash.basic_dash(segment_number, bitrates, average_dwn_time,
                                                                          recent_download_sizes,
                                                                          previous_segment_times, current_bitrate)

                if dash_player.buffer.qsize() > config_client.BASIC_THRESHOLD:
                    delay = dash_player.buffer.qsize() - config_client.BASIC_THRESHOLD
                config_client.LOG.info("Basic-DASH: Selected {} for the segment {}".format(current_bitrate,
                                                                                           segment_number + 1))
            else:
                config_client.LOG.error("Unknown playback type:{}. Continuing with basic playback".format(
                    playback_type))
                current_bitrate, average_dwn_time = basic_dash.basic_dash(segment_number, bitrates, average_dwn_time,
                                                                          segment_download_time, current_bitrate)
        segment_path = read_mpd.get_segment_path(dp_object.video, dp_object.playback_duration,current_bitrate,
                                                 segment_number)
        segment_url = urlparse.urljoin(domain, segment_path)
        config_client.LOG.info("{}: Segment URL = {}".format(playback_type.upper(), segment_url))
        if delay:
            delay_start = time.time()
            config_client.LOG.info("SLEEPING for {}seconds ".format(delay*segment_duration))
            while time.time() - delay_start < (delay * segment_duration):
                time.sleep(1)
            delay = 0
            config_client.LOG.debug("SLEPT for {}seconds ".format(time.time() - delay_start))
        start_time = timeit.default_timer()
        try:
            segment_size, segment_filename = download_segment(segment_url, file_identifier)
            config_client.LOG.info("{}: Downloaded segment {}".format(playback_type.upper(), segment_url))
        except IOError, e:
            config_client.LOG.error("Unable to save segment %s" % e)
            return None
        segment_download_time = timeit.default_timer() - start_time
        previous_segment_times.append(segment_download_time)
        recent_download_sizes.append(segment_size)
        # Updating the JSON information
        segment_name = os.path.split(segment_url)[1]
        if "segment_info" not in config_client.JSON_HANDLE:
            config_client.JSON_HANDLE["segment_info"] = list()
        config_client.JSON_HANDLE["segment_info"].append((segment_name, current_bitrate, segment_size,
                                                          segment_download_time))
        total_downloaded += segment_size
        config_client.LOG.info("{} : The total downloaded = {}, segment_size = {}, segment_number = {}".format(
            playback_type.upper(),
            total_downloaded, segment_size, segment_number))
        segment_info = {'playback_length': dp_object.video['duration']/dp_object.video['timescale'],
                        'size': segment_size,
                        'bitrate': current_bitrate,
                        'data': segment_filename,
                        'URI': segment_url,
                        'segment_number': segment_number}
        segment_duration = segment_info['playback_length']
        dash_player.write(segment_info)
        segment_files.append(segment_filename)
        config_client.LOG.info("Downloaded %s. Size = %s in %s seconds" % (
            segment_url, segment_size, str(segment_download_time)))
        downloaded_duration += segment_duration
        segment_number += 1
        if previous_bitrate:
            if previous_bitrate < current_bitrate:
                config_client.JSON_HANDLE['playback_info']['up_shifts'] += 1
            elif previous_bitrate > current_bitrate:
                config_client.JSON_HANDLE['playback_info']['down_shifts'] += 1
            previous_bitrate = current_bitrate

    # waiting for the player to finish playing
    while dash_player.playback_state not in dash_buffer.EXIT_STATES:
        time.sleep(1)
    write_json()
    if not download:
        clean_files(file_identifier)


def clean_files(folder_path):
    """
    :param folder_path: Local Folder to be deleted
    """
    if os.path.exists(folder_path):
        try:
            for video_file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, video_file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            os.rmdir(folder_path)
        except (WindowsError, OSError), e:
            config_client.LOG.info("Unable to delete the folder {}. {}".format(folder_path, e))
        config_client.LOG.info("Deleted the folder '{}' and its contents".format(folder_path))


def create_arguments(parser):
    """ Adding arguments to the parser """
    parser.add_argument('-m', '--MPD',                   
                        help="Url to the MPD File")
    parser.add_argument('-l', '--LIST', action='store_true',
                        help="List all the representations without downloading the video file.")
    parser.add_argument('-p', '--PLAYBACK',
                        default=DEFAULT_PLAYBACK,
                        help="Playback type (basic)")
    parser.add_argument('-n', '--SEGMENT_LIMIT',
                        default=SEGMENT_LIMIT,
                        help="The Segment number limit. Limits the number of segments taht are downloaded.")
    parser.add_argument('-d', '--DOWNLOAD', action='store_true',
                        default=False,
                        help="Keep the video files after playback. When we set to False all the files are deleted after the video session.")


def get_opener():
    """
    Module to create an Urllib2 opener with the cookies
    :return:
    """
    url_opener = urllib2.build_opener()
    config_client.LOG.info("Cookie info = {}".format(config_client.COOKIE_FIELDS))
    for cookie_field in config_client.COOKIE_FIELDS:
        url_opener.addheaders.append((cookie_field,
                                      config_client.COOKIE_FIELDS[cookie_field]))
    return url_opener


def main():
    """ Main Program wrapper """
    # configure the log file
    # Create arguments
    parser = ArgumentParser(description='Process Client parameters')
    create_arguments(parser)
    args = parser.parse_args()
    globals().update(vars(args))
    configure_log_file(playback_type=PLAYBACK.lower())
    config_client.JSON_HANDLE['playback_type'] = PLAYBACK.lower()
    if not MPD:
        print "ERROR: Please provide the URL to the MPD file. Try Again.."
        return None
    config_client.LOG.info('Downloading MPD file %s' % MPD)
    # Retrieve the MPD files for the video
    mpd_opener = get_opener()
    mpd_file = get_mpd(MPD, mpd_opener)
    domain = get_domain_name(MPD)
    # Reading the MPD file created
    dp_object = read_mpd.read_mpd(mpd_file)
    config_client.LOG.info("The DASH media has %d video representations" % len(dp_object.video))
    if LIST:
        # Print the representations and EXIT
        print_representations(dp_object)
        return None
    else:
        config_client.LOG.critical("Started DASH Playback")
        start_playback(dp_object, domain, "BASIC", DOWNLOAD)

if __name__ == "__main__":
    sys.exit(main())
