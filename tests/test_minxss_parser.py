from minxss_parser import MinxssParser
from example_data import get_example_data
from find_sync_bytes import FindSyncBytes
from numpy.testing import assert_approx_equal

buffer_data = get_example_data(1)
minxss_parser = MinxssParser(buffer_data)


def test_valid_telemetry():
    telemetry = minxss_parser.parse_packet()

    assert isinstance(telemetry, dict)
    assert len(telemetry) == 27

    assert telemetry['FlightModel'] == 1
    assert telemetry['CommandAcceptCount'] == 2691
    assert telemetry['SpacecraftMode'] == 4
    assert telemetry['PointingMode'] == 1
    assert telemetry['Eclipse'] == 0

    assert telemetry['EnableX123'] == 1
    assert telemetry['EnableSps'] == 1

    assert_approx_equal(telemetry['SpsX'], -0.36, significant=2)
    assert_approx_equal(telemetry['SpsY'], 0.16, significant=2)
    assert telemetry['Xp'] == 153.0

    assert_approx_equal(telemetry['CdhBoardTemperature'], 12.25, significant=4)
    assert_approx_equal(telemetry['CommBoardTemperature'], 8.56, significant=3)
    assert_approx_equal(telemetry['MotherboardTemperature'], 8.62, significant=3)
    assert_approx_equal(telemetry['EpsBoardTemperature'], 31.56, significant=4)
    assert_approx_equal(telemetry['SolarPanelMinusYTemperature'], 52.23, significant=4)
    assert_approx_equal(telemetry['SolarPanelPlusXTemperature'], 53.80, significant=4)
    assert_approx_equal(telemetry['SolarPanelPlusYTemperature'], 46.82, significant=4)
    assert_approx_equal(telemetry['BatteryTemperature'], 12.34, significant=4)

    assert_approx_equal(telemetry['BatteryVoltage'], 7.97, significant=3)
    assert_approx_equal(telemetry['BatteryChargeCurrent'], 347.4, significant=4)
    assert_approx_equal(telemetry['BatteryDischargeCurrent'], 9.54, significant=3)

    assert_approx_equal(telemetry['SolarPanelMinusYCurrent'], 134, significant=3)
    assert_approx_equal(telemetry['SolarPanelPlusXCurrent'], 536, significant=3)
    assert_approx_equal(telemetry['SolarPanelPlusYCurrent'], 136, significant=3)

    assert_approx_equal(telemetry['SolarPanelMinusYVoltage'], 16.9, significant=3)
    assert_approx_equal(telemetry['SolarPanelPlusXVoltage'], 9.77, significant=3)
    assert_approx_equal(telemetry['SolarPanelPlusYVoltage'], 16.5, significant=3)


def test_invalid_packet():
    normal_packet = minxss_parser.minxss_packet

    no_start_sync_packet = normal_packet[1:]
    minxss_parser.minxss_packet = no_start_sync_packet
    assert minxss_parser.is_valid_packet() is False

    no_stop_sync_packet = normal_packet[0:-2]
    minxss_parser.minxss_packet = no_stop_sync_packet
    assert minxss_parser.is_valid_packet() is False

    wrong_length_packet = normal_packet[0:20] + normal_packet[22:]
    minxss_parser.minxss_packet = wrong_length_packet
    assert minxss_parser.is_valid_packet() is False

    minxss_parser.minxss_packet = normal_packet


def test_shift_packet_to_sync_start():
    fsb = FindSyncBytes()

    # Check that we're starting from the correct position
    assert minxss_parser.minxss_packet[0:2] == fsb.start_sync_bytes

    # Prepend an extra byte so the sync bytes are no longer at the start
    minxss_parser.minxss_packet[:0] = bytearray([0x00])
    assert minxss_parser.minxss_packet[0:2] != fsb.start_sync_bytes

    minxss_parser.ensure_packet_starts_at_sync()
    assert minxss_parser.minxss_packet[0:2] == fsb.start_sync_bytes


def test_decode_bytes():
    assert minxss_parser.decode_bytes(bytearray([0xFF, 0xDC])) == -8961
    assert minxss_parser.decode_bytes(bytearray([0xFF, 0xDC]), return_unsigned_int=True) == 56575
