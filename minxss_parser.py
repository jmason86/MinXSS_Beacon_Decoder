"""Parse MinXSS packet"""
__author__ = "James Paul Mason"
__contact__ = "jmason86@gmail.com"

from numpy import uint8, int16, uint16
from find_sync_bytes import FindSyncBytes
from logger import Logger


class MinxssParser:
    def __init__(self, minxss_packet):
        self.minxss_packet = minxss_packet  # [bytearray]: Un-decoded data to be parsed
        self.log = Logger().create_log()
        self.expected_packet_length = 252

    def parse_packet(self):
        """
        Returns decoded telemetry as a dictionary
        """
        if not self.is_valid_packet():
            return None

        self.ensure_packet_starts_at_sync()

        telemetry = dict()

        # Note: The [n: n + 2] instead of [n: n + 1] is because python slicing cuts short
        # e.g., to get bytes at indices 3 and 4, you don't do minxss_packet[3:4], you have to do minxss_packet[3:5]
        telemetry['FlightModel'] = self.decode_flight_model(self.minxss_packet[51])                        # [Unitless]
        telemetry['CommandAcceptCount'] = self.decode_command_accept_count(self.minxss_packet[16:16 + 2])  # [#]
        telemetry['SpacecraftMode'] = self.decode_spacecraft_mode(self.minxss_packet[12])                  # [Unitless]
        telemetry['PointingMode'] = self.decode_pointing_mode(self.minxss_packet[13])                      # [Unitless]
        telemetry['Eclipse'] = self.decode_eclipse(self.minxss_packet[12])                                 # [Boolean]

        telemetry['EnableX123'] = self.decode_enable_x123(self.minxss_packet[88:88 + 2])  # [Boolean]
        telemetry['EnableSps'] = self.decode_enable_sps(self.minxss_packet[88:88 + 2])    # [Boolean]

        telemetry['SpsX'] = self.decode_sps(self.minxss_packet[204:204 + 2])  # [deg]
        telemetry['SpsY'] = self.decode_sps(self.minxss_packet[206:206 + 2])  # [deg]
        telemetry['Xp'] = self.decode_xp(self.minxss_packet[192:192 + 4])     # [DN]

        telemetry['CdhBoardTemperature'] = self.decode_temperature(self.minxss_packet[86:86 + 2])                        # [deg C]
        telemetry['CommBoardTemperature'] = self.decode_temperature(self.minxss_packet[122:122 + 2])                     # [deg C]
        telemetry['MotherboardTemperature'] = self.decode_temperature(self.minxss_packet[124:124 + 2])                   # [deg C]
        telemetry['EpsBoardTemperature'] = self.decode_temperature(self.minxss_packet[128:128 + 2])                      # [deg C]
        telemetry['SolarPanelMinusYTemperature'] = self.decode_temperature_solar_panel(self.minxss_packet[160:160 + 2])  # [deg C]
        telemetry['SolarPanelPlusXTemperature'] = self.decode_temperature_solar_panel(self.minxss_packet[162:162 + 2])   # [deg C]
        telemetry['SolarPanelPlusYTemperature'] = self.decode_temperature_solar_panel(self.minxss_packet[164:164 + 2])   # [deg C]
        telemetry['BatteryTemperature'] = self.decode_temperature_battery(self.minxss_packet[174:174 + 2])               # [deg C]

        telemetry['BatteryVoltage'] = self.decode_battery_voltage(self.minxss_packet[132:132 + 2])           # [V]
        telemetry['BatteryChargeCurrent'] = self.decode_battery_current(self.minxss_packet[168:168 + 2])     # [mA]
        telemetry['BatteryDischargeCurrent'] = self.decode_battery_current(self.minxss_packet[172:172 + 2])  # [mA]
        
        telemetry['SolarPanelMinusYCurrent'] = self.decode_solar_array_current(self.minxss_packet[136:136 + 2])  # [mA]
        telemetry['SolarPanelPlusXCurrent'] = self.decode_solar_array_current(self.minxss_packet[140:140 + 2])   # [mA]
        telemetry['SolarPanelPlusYCurrent'] = self.decode_solar_array_current(self.minxss_packet[144:144 + 2])   # [mA]
        
        telemetry['SolarPanelMinusYVoltage'] = self.decode_solar_array_voltage(self.minxss_packet[138:138 + 2])  # [V]
        telemetry['SolarPanelPlusXVoltage'] = self.decode_solar_array_voltage(self.minxss_packet[142:142 + 2])   # [V]
        telemetry['SolarPanelPlusYVoltage'] = self.decode_solar_array_voltage(self.minxss_packet[146:146 + 2])   # [V]
        
        self.log.info("From MinXSS parser:")
        self.log.info(telemetry)
        return telemetry

    def is_valid_packet(self):
        fsb = FindSyncBytes()
        sync_start_index = fsb.find_sync_start_index(self.minxss_packet)
        sync_stop_index = fsb.find_sync_stop_index(self.minxss_packet)
        packet_length = sync_stop_index - sync_start_index

        if sync_start_index == -1:
            self.log.error('Invalid packet detected. No sync start pattern found. Returning.')
            return False
        if sync_stop_index == -1:
            self.log.error('Invalid packet detected. No sync stop pattern found. Returning.')
            return False
        if packet_length != self.expected_packet_length:
            self.log.error('Invalid packet detected. Packet length is {0} but expected to be {1}. Returning.'.format(packet_length, self.expected_packet_length))
            return False

        return True

    def ensure_packet_starts_at_sync(self):
        fsb = FindSyncBytes()
        sync_offset = fsb.find_sync_start_index(self.minxss_packet)
        self.minxss_packet = self.minxss_packet[sync_offset:len(self.minxss_packet)]

    def decode_bytes(self, bytearray_temp, return_unsigned_int=False):
        """
        Combine several bytes corresponding to a single telemetry point to a single integer
        # Input:
        #   bytearray_temp [bytearray]: The bytes corresponding to the telemetry to decode.
        #                               Can accept any number of bytes but do not expect more than 4
        # Flags:
        #   return_unsigned_int: If set, return an unsigned integer instead of the default signed integer
        # Output:
        #   telemetry_point_raw [int]: The single integer for the telemetry point to be converted to human-readable by
                                       the calling function
        """
        if len(bytearray_temp) == 1:
            telemetry_point_raw = bytearray_temp
        elif len(bytearray_temp) == 2:
            telemetry_point_raw = (uint8(bytearray_temp[1]) << 8) | uint8(bytearray_temp[0])
        elif len(bytearray_temp) == 4:
            telemetry_point_raw = (uint8(bytearray_temp[3]) << 24) | (uint8(bytearray_temp[2] << 16)) | \
                                  (uint8(bytearray_temp[1] << 8)) | (uint8(bytearray_temp[0] << 0))
        else:
            self.log.debug("More bytes than expected")
            return None

        if return_unsigned_int:
            return uint16(telemetry_point_raw)
        else:
            return int16(telemetry_point_raw)

    @staticmethod
    def decode_flight_model(bytearray_temp):
        flight_model = (bytearray_temp & 0x0030) >> 4  # [Unitless]

        # Fix mistaken flight model number in final flight software burn
        if flight_model == 3:
            flight_model = 2
        elif flight_model == 4:
            flight_model = 3  # This is the engineering test unit (AKA FlatSat)
        return flight_model
    
    def decode_command_accept_count(self, bytearray_temp):
        return self.decode_bytes(bytearray_temp)  # [#]
    
    @staticmethod
    def decode_spacecraft_mode(bytearray_temp):
        return bytearray_temp & 0x07  # [Unitless]
    
    @staticmethod
    def decode_pointing_mode(bytearray_temp):
        return bytearray_temp & 0x01  # [Unitless]
    
    def decode_enable_x123(self, bytearray_temp):
        decoded_byte = self.decode_bytes(bytearray_temp)
        return (decoded_byte & 0x0002) >> 1  # [Boolean]
    
    def decode_enable_sps(self, bytearray_temp):
        decoded_byte = self.decode_bytes(bytearray_temp)
        return (decoded_byte & 0x0004) >> 2  # [Boolean]
    
    def decode_sps(self, bytearray_temp):
        return self.decode_bytes(bytearray_temp) / 1e4 * 3.0  # [deg]

    @staticmethod
    def decode_eclipse(bytearray_temp):
        return (bytearray_temp & 0x08) >> 3  # [Boolean]

    def decode_xp(self, bytearray_temp):
        return self.decode_bytes(bytearray_temp, return_unsigned_int=True)  # [DN]
    
    def decode_temperature(self, bytearray_temp):
        return self.decode_bytes(bytearray_temp) / 256.0  # [deg C]
    
    def decode_temperature_battery(self, bytearray_temp):
        return self.decode_bytes(bytearray_temp, return_unsigned_int=True) * 0.18766 - 250.2  # [deg C]
    
    def decode_temperature_solar_panel(self, bytearray_temp):
        return self.decode_bytes(bytearray_temp, return_unsigned_int=True) * 0.1744 - 216.0  # [deg C]
    
    def decode_battery_voltage(self, bytearray_temp):
        return self.decode_bytes(bytearray_temp, return_unsigned_int=True) / 6415.0  # [V]
    
    def decode_battery_current(self, bytearray_temp):
        return self.decode_bytes(bytearray_temp, return_unsigned_int=True) * 3.5568 - 61.6  # [mA]
    
    def decode_solar_array_current(self, bytearray_temp):
        return self.decode_bytes(bytearray_temp, return_unsigned_int=True) * 163.8 / 327.68  # [mA]
    
    def decode_solar_array_voltage(self, bytearray_temp):
        return self.decode_bytes(bytearray_temp, return_unsigned_int=True) * 32.76 / 32768.0  # [V]
