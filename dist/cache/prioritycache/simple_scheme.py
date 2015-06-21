__author__ = 'pjuluri'

"""
In the simple scheme we prefetch the next segment of the same bitrate
"""
import os
SEGMENT_TEMPLATE = {'TheSwissAccount': 'TheSwissAccount_4s',
                    'BigBuckBunny' : 'BigBuckBunny_4s'}

def get_next_bitrate(request_path):
    """
     sample_request = /media/TheSwissAccount/4sec/swiss_88745bps/TheSwissAccount_4s1.m4s
    :param file_path: File request path
    :return: return the request for the next bitrate
    """
    request = request_path.split('/')
    video_id, bitrate, segment = request[1], request[-2], request[-1]
    next_segment = None
    if 'init' in segment:
        next_segment = '1'
    else:
        segment_number = segment.replace(SEGMENT_TEMPLATE[video_id], '')
        segment_number = segment_number.replace('.m4s', '')
        segment_number = ''.join([i for i in segment_number if i.isdigit()])
        segment_number = int(segment_number)
        next_segment = str(segment_number + 1)
    next_segment_name = ''.join((SEGMENT_TEMPLATE[video_id], next_segment, '.m4s'))
    next_file_path = '/'.join((os.path.dirname(request_path), next_segment_name))
    print 'NEXT is', next_file_path
    return next_file_path












