from minxss_parser import MinxssParser
from example_data import get_example_data
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

