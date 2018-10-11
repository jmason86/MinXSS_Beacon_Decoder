"""Parse MinXSS packet"""
__author__ = "James Paul Mason"
__contact__ = "jmason86@gmail.com"

from numpy import int8, uint8, int16, uint16, int32, uint32
from find_sync_bytes import FindSyncBytes


class MinxssParser:
    def __init__(self, minxss_packet, log):
        self.minxss_packet = minxss_packet  # [bytearray]: Un-decoded data to be parsed
        self.log = log

    def parse_packet(self):
        """
        Returns decoded telemetry as a dictionary
        """
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

    def ensure_packet_starts_at_sync(self):
        fsb = FindSyncBytes()
        sync_offset = fsb.find_sync_start_index(self.minxss_packet)
        if sync_offset != -1:
            self.minxss_packet = self.minxss_packet[sync_offset:len(self.minxss_packet)]
        else:
            self.log.error("No start sync bytes found in minxss_parser, exiting.")
            return None

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
            return bytearray_temp
        elif len(bytearray_temp) == 2:
            if return_unsigned_int:
                return uint16((int8(bytearray_temp[1]) << 8) | uint8(bytearray_temp[0]))
            else:
                return int16((uint8(bytearray_temp[1]) << 8) | uint8(bytearray_temp[0]))
        elif len(bytearray_temp) == 4:
            if return_unsigned_int:
                return uint32((uint8(bytearray_temp[3]) << 24) | (uint8(bytearray_temp[2] << 16)) |
                              (uint8(bytearray_temp[1] << 8)) | (uint8(bytearray_temp[0] << 0)))
            else:
                return int32((uint8(bytearray_temp[3]) << 24) | (uint8(bytearray_temp[2] << 16)) |
                             (uint8(bytearray_temp[1] << 8)) | (uint8(bytearray_temp[0] << 0)))
        else:
            self.log.debug("More bytes than expected")
                
    ##
    # The following functions all have the same purpose: to convert raw bytes to human-readable output.
    # Only the units will be commented on. The function and variable names are explicit and verbose for clarity.
    ##
    
    # Purpose:
    #   Convert raw telemetry to human-readable number in human-readable units
    # Input:
    #   bytearrayTemp [bytearray]: The bytes corresponding to the telemetry to decode.
    #                              Can accept any number of bytes but do not expect more than 4
    # Output:
    #   telemetryPoint [int, float, string, as appropriate]: The telemetry point in human-readable form and units
    #
    
    def decode_flight_model(self, bytearrayTemp):
        flight_model = (bytearrayTemp & 0x0030) >> 4  # [Unitless]

        # Fix mistaken flight model number in final flight software burn
        if flight_model == 3:
            flight_model = 2
        elif flight_model == 4:
            flight_model = 3  # This is the engineering test unit (AKA FlatSat)
        return flight_model
    
    def decode_command_accept_count(self, bytearrayTemp):
        return self.decode_bytes(bytearrayTemp) # [#]
    
    def decode_spacecraft_mode(self, bytearrayTemp):
        return (bytearrayTemp & 0x07) # [Unitless]
    
    def decode_pointing_mode(self, bytearrayTemp):
        return (bytearrayTemp & 0x01) # [Unitless]
    
    def decode_enable_x123(self, bytearrayTemp):
        decodedByte = self.decode_bytes(bytearrayTemp)
        return (decodedByte & 0x0002) >> 1 # [Boolean]
    
    def decode_enable_sps(self, bytearrayTemp):
        decodedByte = self.decode_bytes(bytearrayTemp)
        return (decodedByte & 0x0004) >> 2 # [Boolean]
    
    def decode_sps(self, bytearrayTemp):
        return self.decode_bytes(bytearrayTemp) / 1e4 * 3.0 # [deg]
    
    def decode_eclipse(self, bytearrayTemp):
        return (bytearrayTemp & 0x08) >> 3

    def decode_xp(self, bytearrayTemp):
        return self.decode_bytes(bytearrayTemp, return_unsigned_int=True) # [DN]
    
    def decode_temperature(self, bytearrayTemp):
        return self.decode_bytes(bytearrayTemp) / 256.0 # [deg C]
    
    def decode_temperature_battery(self, bytearrayTemp):
        return self.decode_bytes(bytearrayTemp, return_unsigned_int=True) * 0.18766 - 250.2 # [deg C]
    
    def decode_temperature_solar_panel(self, bytearrayTemp):
        return self.decode_bytes(bytearrayTemp, return_unsigned_int=True) * 0.1744 - 216.0 # [deg C]
    
    def decode_battery_voltage(self, bytearrayTemp):
        return self.decode_bytes(bytearrayTemp, return_unsigned_int=True) / 6415.0 # [V]
    
    def decode_battery_current(self, bytearrayTemp):
        return self.decode_bytes(bytearrayTemp, return_unsigned_int=True) * 3.5568 - 61.6 # [mA]
    
    def decode_solar_array_current(self, bytearrayTemp):
        return self.decode_bytes(bytearrayTemp, return_unsigned_int=True) * 163.8 / 327.68 # [mA]
    
    def decode_solar_array_voltage(self, bytearrayTemp):
        return self.decode_bytes(bytearrayTemp, return_unsigned_int=True) * 32.76 / 32768.0 # [V]
    
    ##
    # End byte->human-readable conversion functions
    ##
