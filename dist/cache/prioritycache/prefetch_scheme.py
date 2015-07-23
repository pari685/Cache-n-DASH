__author__ = 'pjuluri'

"""
The prefetch schemes used at the Cache
    BASIC: Prefetch the next segment of the current bitrate
    SMART: Prefetch the next segment based on throughput
"""
import os
import config_cdash


def get_prefetch(video_request, pre_fetch_scheme, throughput):
    """
    sample_request = /media/TheSwissAccount/4sec/swiss_88745bps/TheSwissAccount_4s1.m4s
    :param file_path: File request path
    :return: return the request for the next bitrate
    """
    segment_number, current_bitrate, video_id, available_bitrates = get_segment_info(video_request)
    if 'init' in video_request:
        next_segment = '1'
        next_bitrate = available_bitrates[0]
    elif 'SMART' in pre_fetch_scheme.upper():
        # Check if we need to increase or decrease bitrate
        config_cdash.LOG.info('Pre-fetch with SMART throughput = {}'.format(throughput))
        if throughput > current_bitrate * config_cdash.BASIC_UPPER_THRESHOLD:
            if current_bitrate == available_bitrates[-1]:
                next_bitrate = current_bitrate
            else:
                # if the bitrate is not at maximum then select the next higher bitrate
                try:
                    current_index = available_bitrates.index(current_bitrate)
                    next_bitrate = available_bitrates[current_index + 1]
                except ValueError:
                    current_index = available_bitrates[0]
        else:
            for index, bitrate in enumerate(available_bitrates[1:], 1):
                if throughput > bitrate * config_cdash.BASIC_UPPER_THRESHOLD:
                    next_bitrate = bitrate
                else:
                    next_bitrate = available_bitrates[index - 1]
                break
    else:
        config_cdash.LOG.info('Pre-fetch with BASIC')
        next_bitrate = current_bitrate
    next_segment = str(segment_number + 1)
    next_segment_name = ''.join((config_cdash.VIDEO_CACHE_CONTENT[video_id]['string-match'], next_segment, '.m4s'))
    current_dir = os.path.dirname(video_request)
    next_dir = current_dir.replace(str(current_bitrate), str(next_bitrate))
    next_file_path = '/'.join((next_dir, next_segment_name))
    config_cdash.LOG.info("Using {} pre_fetch_scheme the next_bitrate = {} and next_file_path = {}".format(
        pre_fetch_scheme, next_bitrate, next_file_path))
    return next_file_path, next_bitrate


def get_segment_info(url):
    """
    Module to parse the URL to retrieve the segment number and bitrate
    Example: 'swiss_88745bps/TheSwissAccount_4s1.m4s' returns (1, 88745)
    :param url: Segment URL (Eg: 'swiss_88745bps/TheSwissAccount_4s1.m4s)
    :return: A tuple with Segment_number, bitrate
    """
    video_request_array = url.split("/")
    video_id, bitrate_string = video_request_array[0].split("_")

    # Parse the segment number
    segment_string = video_request_array[1]
    segment_number = segment_string.replace(config_cdash.VIDEO_CACHE_CONTENT[video_id]['string-match'], '')
    segment_number = segment_number.replace('.m4s', '')
    segment_number = int(''.join([i for i in segment_number if i.isdigit()]))

    available_bitrates = config_cdash.VIDEO_CACHE_CONTENT[video_id]['available-bitrate']

    # parse the bitrate
    bitrate = int("".join([ch for ch in bitrate_string if ch.isdigit()]))
    return segment_number, bitrate, video_id, available_bitrates








