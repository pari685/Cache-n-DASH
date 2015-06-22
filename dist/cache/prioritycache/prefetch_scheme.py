__author__ = 'pjuluri'

"""
In the simple scheme we prefetch the next segment of the same bitrate
"""
import os
import re
import config_cdash

def get_next_simple(video_request):
    """
     sample_request = /media/TheSwissAccount/4sec/swiss_88745bps/TheSwissAccount_4s1.m4s
    :param file_path: File request path
    :return: return the request for the next bitrate
    """
    video_request_array = video_request.split("/")
    # checking if the requested video name is in the server i.e the key matches the request
    bitrate_request = video_request_array[0].split("_")
    video_id = bitrate_request[0]
    print video_id
    segment_string = video_request_array[1]
    if 'init' in video_request:
        next_segment = '1'
    else:
        segment_number = segment_string.replace(config_cdash.VIDEO_CACHE_CONTENT[video_id]['string-match'], '')
        segment_number = segment_number.replace('.m4s', '')
        segment_number = ''.join([i for i in segment_number if i.isdigit()])
        segment_number = int(segment_number)
        next_segment = str(segment_number + 1)
    next_segment_name = ''.join((config_cdash.VIDEO_CACHE_CONTENT[video_id]['string-match'], next_segment, '.m4s'))
    next_file_path = '/'.join((os.path.dirname(video_request), next_segment_name))
    return next_file_path












