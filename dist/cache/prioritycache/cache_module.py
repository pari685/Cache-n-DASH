import sys
import re
import os
import config_cdash


def segment_exists(video_segment):
    """ Module to check if a given segment exisst in the cache """
    video_segment_name = video_segment.replace('/', '-')
    video_path = os.path.join(config_cdash.VIDEO_FOLDER, video_segment_name)
    if os.path.exists(video_path):
        config_cdash.LOG.info('Segment already in cache {}'.format(video_path))
        return True
    return False


def check_content_server(video_request):
    """ Module to check if the request is in the content server
    """
    video_request_array = video_request.split("/")
    # checking if the requested video name is in the server i.e the key matches the request
    bitrate_request = video_request_array[0].split("_")
    video_id = bitrate_request[0]
    bitrate_array = re.split('(\d+)', bitrate_request[1])
    bitrate = int(bitrate_array[1])
    # splitting BigBuckBunny_4s1.m4s into BigBuckBunny and 4s1.m4s
    if video_id in config_cdash.VIDEO_CACHE_CONTENT:
        if bitrate in config_cdash.VIDEO_CACHE_CONTENT[video_id]['available-bitrate']:
            if 'init' in video_request:
                return True
            else:
                segment_number = video_request_array[1].replace(
                    config_cdash.VIDEO_CACHE_CONTENT[video_id]['string-match'], '')
                segment_number = int(segment_number.replace('.m4s', ''))
                start, end = config_cdash.VIDEO_CACHE_CONTENT[video_id]['segment-range']
                if start <= segment_number <= end:
                    return True
            print bitrate, segment_number, start, end
    return False

def test():
    print check_content_server("bunny_88783bps/BigBuckBunny_4s4.m4s")
    print check_content_server("bunny_45226bps/BigBuckBunny_4s4.m4s")

if __name__ == "__main__":
    sys.exit(test())