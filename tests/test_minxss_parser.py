from minxss_parser import MinxssParser
from example_data import get_example_data


def test_parser():
    buffer_data = get_example_data(0)
    minxss_parser = MinxssParser(buffer_data)
    telemetry = minxss_parser.parse_packet()
    print(telemetry)
