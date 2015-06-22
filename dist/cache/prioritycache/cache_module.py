import sys
import re

VIDEO_CACHE_CONTENT = {
    'BigBuckBunny': {'available-bitrate': [45226, 88783, 128503, 177437, 217761, 255865, 323047, 378355, 509091,
                                            577751, 782553, 1008699, 1207152, 1473801, 2087347, 2409742, 2944291,
                                            3340509, 3613836, 3936261],
                     'segment-range': [1, 150],
                     'string-match': 'BigBuckBunny_4s'},
    'OfForestAndMen': {'available-bitrate': [46516, 91651, 136761, 185092, 231141, 276163, 365184, 461029, 552051,
                                             642534,824821, 1005167, 1260896, 1512020, 1754001, 2143443, 2506133,
                                             3170853, 3744774],
                       'segment-range':[1, 114],
                       'string-match': 'OfForestAndMen_4s'},
    'TheSwissAccount': {'available-bitrate': [88745, 128171, 172453, 215003, 255984, 330491, 430406, 600840, 754258,
                                              930297, 1323244, 1716694, 1988387, 2708994, 3430035, 3817613, 4003428],
                        'segment-range': [4,78,34,20],
                        'string-match': 'TheSwissAccount_4s'},
    'Valkaama': {'available-bitrate': [45679, 85914, 118584, 172627, 209596, 242301, 298523, 1861036, 2317655, 2755290,
                                       3522543, 4118338, 4561266, 432505, 505903, 574104, 811486, 983335, 1217742,
                                       1422377],
                 'segment-range': [1, 1162],
                 'string-match': 'Valkaama_4'},
    'ElephantsDream': {'available-bitrate': [45791, 89889, 129426, 179119, 220743, 259179, 323473, 375852, 516656,
                                             582757, 792489, 1016017, 1197604, 1456380, 2087288, 2394379, 2908119,
                                             3339937, 3666428, 4066615],
                       'segment-range': [1, 164],
                       'string-match': 'ElephantsDream_4s'},
    'RedBullPlayStreets': {'available-bitrate': [100733, 149211, 200933, 250302, 299039, 395090, 500459, 700159, 891912,
                                                 1171990, 1498197, 1991890, 2465785, 2995811, 3992562, 4979124,
                                                 5936225],
                           'segment-range': [1, 10],
                           'string-match': 'RedBull_4'},
    'TearsOfSteel': {'available-bitrate': [101, 65509, 129510, 191511, 253270, 504741, 807450, 1506971, 2416099,
                                           3004351, 4011653, 6025488, 10045361],
                     'segment-range': [1, 184],
                     'string-match': 'TearsOfSteel_4s_'},
    }


def check_content_server(video_request):
    """ Module to check if the request is in the content server
    """
    video_request_array = video_request.split("/")
    #checking if the requested video name is in the server i.e the key matches the request
    bitrate_request = video_request_array[3].split("_")
    bitrate_array = re.split('(\d+)', bitrate_request[1])
    bitrate = int(bitrate_array[1])
    # splitting BigBuckBunny_4s1.m4s into BigBuckBunny and 4s1.m4s
    print bitrate
    if video_request_array[1] in VIDEO_CACHE_CONTENT:
        if bitrate in VIDEO_CACHE_CONTENT[video_request_array[1]]['available-bitrate']:
            if 'init' in video_request:
                return True
            else:
                segment_number = video_request_array[4].replace(
                    VIDEO_CACHE_CONTENT[video_request_array[1]]['string-match'], '')
                segment_number = int(segment_number.replace('.m4s', ''))
                start, end = VIDEO_CACHE_CONTENT[video_request_array[1]]['segment-range']
                if start <= segment_number <= end:
                    return True
            print bitrate, segment_number, start, end
    return False

def test():
    print check_content_server("/BigBuckBunny/4sec/bunny_288783bps/BigBuckBunny_4s4.m4s")
    print check_content_server("/TearsOfSteel/4sec/tos_191511bps/TearsOfSteel_4s_82.m4s")
    print check_content_server("/OfForestAndMen/4sec/forest_46516bps/OfForestAndMen_4s_init.mp4")

if __name__ == "__main__":
    sys.exit(test())
