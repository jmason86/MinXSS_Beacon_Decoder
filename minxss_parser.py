"""Parse MinXSS packet"""
__author__ = "James Paul Mason"
__contact__ = "jmason86@gmail.com"

import os
import logging
import pdb, binascii

class Minxss_Parser():
    def __init__(self, minxssSerialData, log):
        self.log = log # debug log

    # Purpose:
    #   Top level wrapper function to take serial data and return parsed and interpretted telemetry as a dictionary
    # Input:
    #   minxssSerialData [bytearray]: The direct output of the python serial line (connect_serial_decode_kiss.read()), or simulated data in that format
    # Output:
    #   selectedTelemetryDictionary [dictionary]: The telemetry with key/value pairs
    #
    def parsePacket(self, minxssSerialData):
        # Find the sync bytes (0x08, 0x19), reframe the packet to start after sync
        syncOffset = self.findSyncIndex(minxssSerialData)
        if syncOffset == -1:
            self.log.info("No sync bytes found")
            return -1
        else:
            minxssSerialData = minxssSerialData[syncOffset:len(minxssSerialData)]
        
        # Prepare a dictionary for storage of telemetry points
        selectedTelemetryDictionary = {}
        
        # Get the telemetry points
        # Note: Second index in range of minxssSerialData must be +1 what you'd normally expect because python is wonky
        # For example, to grab bytes at indices 3 and 4, you don't do minxssSerialData[3:4], you have to do minxssSerialData[3:5]
        selectedTelemetryDictionary['5vLineVoltage'] = self.decodeBytesCdh5v(minxssSerialData[82:82+2])                      # [V]
        selectedTelemetryDictionary['CommBoardTemperature'] = self.decodeBytesTemperature(minxssSerialData[122:122+2])       # [deg C]
        selectedTelemetryDictionary['MotherboardTemperature'] = self.decodeBytesTemperature(minxssSerialData[124:124+2])     # [deg C]
        selectedTelemetryDictionary['EpsBoardTemperature'] = self.decodeBytesTemperature(minxssSerialData[128:128+2])        # [deg C]
        selectedTelemetryDictionary['BatteryVoltage'] = self.decodeBytesFuelGaugeBatteryVoltage(minxssSerialData[132:132+2]) # [V]
        selectedTelemetryDictionary['SolarArray-YCurrent'] = self.decodeBytesSolarArrayCurrent(minxssSerialData[136:136+2])  # [mA]
        selectedTelemetryDictionary['SolarArray+XCurrent'] = self.decodeBytesSolarArrayCurrent(minxssSerialData[140:140+2])  # [mA]
        selectedTelemetryDictionary['SolarArray+YCurrent'] = self.decodeBytesSolarArrayCurrent(minxssSerialData[144:144+2])  # [mA]
        selectedTelemetryDictionary['SolarArray-YVoltage'] = self.decodeBytesSolarArrayVoltage(minxssSerialData[138:138+2])  # [V]
        selectedTelemetryDictionary['SolarArray+XVoltage'] = self.decodeBytesSolarArrayVoltage(minxssSerialData[142:142+2])  # [V]
        selectedTelemetryDictionary['SolarArray+YVoltage'] = self.decodeBytesSolarArrayVoltage(minxssSerialData[146:146+2])  # [V]
        
        self.log.info("From MinXSS parser:")
        self.log.info(selectedTelemetryDictionary)
        return selectedTelemetryDictionary

    # Purpose:
    #   Find the start of the MinXSS packet and return the index within minxssSerialData
    # Input:
    #   minxssSerialData [bytearray]: The direct output of the python serial line (connect_serial_decode_kiss.read()), or simulated data in that format
    # Output:
    #   packetStartIndex [int]: The index within minxssSerialData where the sync bytes were found. -1 if not found.
    #
    def findSyncIndex(self, minxssSerialData):
        syncBytes = bytearray([0x08, 0x19]) # This is actually the CCSDS start and then the housekeeping packet APID
        packetStartIndex = bytearray(minxssSerialData).find(syncBytes)
        return packetStartIndex
    
    # Purpose:
    #   Combine several bytes corresponding to a single telemetry point to a single integer
    # Input:
    #   bytearrayTemp [bytearray]: The bytes corresponding to the telemetry to decode.
    #                              Can accept any number of bytes but do not expect more than 4
    # Output:
    #   telemetryPointRaw [int]: The single integer for the telemetry point to be converted to human-readable by the appropriate function
    #
    def decodeBytes(self, bytearrayTemp):
        # Check input
        if len(bytearrayTemp) > 4:
            self.log.debug("More input bytes than the expected 4 for a MinXSS telemetry point")
        
        # Loop through bytes and shift them progressively more and sum them up so that they create a single word
        numberOfBitsToShiftBy = 0
        telemetryPointRaw = 0
        for byte in bytearrayTemp:
            shiftedByte = byte << numberOfBitsToShiftBy
            telemetryPointRaw += shiftedByte
            numberOfBitsToShiftBy += 8

        return telemetryPointRaw

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
    
    def decodeBytesCdh5v(self, bytearrayTemp):
        return self.decodeBytes(bytearrayTemp) * 6.71 / 4096. # [V]
    
    def decodeBytesTemperature(self, bytearrayTemp):
        return self.decodeBytes(bytearrayTemp) / 256.0 # [deg C]
    
    def decodeBytesFuelGaugeBatteryVoltage(self, bytearrayTemp):
        return self.decodeBytes(bytearrayTemp) / 6415.0 # [V]
    
    def decodeBytesSolarArrayCurrent(self, bytearrayTemp):
        return self.decodeBytes(bytearrayTemp) * 163.8 / 327.68 # [mA]
    
    def decodeBytesSolarArrayVoltage(self, bytearrayTemp):
        return self.decodeBytes(bytearrayTemp) * 32.76 / 32768.0 # [V]
    
    ##
    # End byte->human-readable conversion functions
    ##
    
    # Purpose:
    #   Test parsing a packet
    # Input:
    #   minxssSerialData [bytearray]: The direct output of the python serial line (connect_serial_decode_kiss.read()), or simulated data in that format
    # Output:
    #   ... not sure yet
    #
    def testParsePacket(self, minxssSerialData, log):
        log.info("Testing MinXSS packet parse")
        selectedTelemetryDictionary = self.parsePacket(minxssSerialData)
        print selectedTelemetryDictionary
        log.info(selectedTelemetryDictionary)

# Purpose:
#   If called directly from Unix, just do a test
#
if __name__ == '__main__':
    # Create a typical telemetry packet as received by the serial line
    exampleData = bytearray([0xc0, 0x00, 0x9a, 0x92, 0x00, 0xb0, 0xa6, 0x64, 0x60, 0x86,
                             0xa2, 0x40, 0x40, 0x40, 0x40, 0xe1, 0x03, 0xf0, 0x08, 0x19,
                             0xc1, 0x6f, 0x00, 0xf7, 0xf1, 0x34, 0xd6, 0x45, 0x47, 0x02,
                             0x0a, 0x86, 0x4b, 0x00, 0x0c, 0x00, 0x01, 0x00, 0x2e, 0x74,
                             0x01, 0x03, 0x30, 0x03, 0x00, 0x03, 0x79, 0x00, 0x00, 0x01,
                             0xfa, 0xc7, 0x10, 0x01, 0x03, 0x00, 0x00, 0x01, 0x5a, 0x80,
                             0x04, 0x01, 0x00, 0x00, 0x00, 0x92, 0x00, 0x00, 0x00, 0x21,
                             0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00,
                             0x00, 0x01, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x5f, 0x00,
                             0x47, 0x13, 0x00, 0x00, 0x0a, 0x80, 0xf6, 0x01, 0xe2, 0x03,
                             0xd3, 0x0b, 0x06, 0x08, 0x90, 0x18, 0x05, 0x04, 0x00, 0x00,
                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00,
                             0x00, 0x00, 0x8e, 0x01, 0x13, 0x00, 0x6d, 0x00, 0x00, 0x64,
                             0x88, 0x01, 0x00, 0x00, 0xac, 0x25, 0x01, 0x00, 0x07, 0x0b,
                             0x20, 0x17, 0x40, 0x15, 0x90, 0x15, 0x80, 0x17, 0x40, 0x18,
                             0xe0, 0xce, 0x58, 0x61, 0x08, 0x00, 0x78, 0x07, 0x08, 0x00,
                             0x80, 0x06, 0x08, 0x00, 0x30, 0x06, 0x18, 0x00, 0x50, 0x20,
                             0x30, 0x01, 0x90, 0x0d, 0x18, 0x00, 0x78, 0x13, 0x4d, 0x05,
                             0x44, 0x05, 0x51, 0x05, 0x09, 0x08, 0x14, 0x00, 0x9e, 0x05,
                             0x6c, 0x00, 0xa0, 0x05, 0xf3, 0x01, 0x5c, 0x00, 0x4f, 0x02,
                             0x52, 0x02, 0x53, 0x01, 0x53, 0x01, 0x33, 0x01, 0x00, 0x00,
                             0x08, 0x01, 0x00, 0x00, 0x7e, 0x00, 0x00, 0x00, 0xcd, 0x00,
                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                             0x00, 0x00, 0xc7, 0x2f, 0x20, 0x12, 0xd8, 0x00, 0x00, 0x00,
                             0x05, 0x07, 0x02, 0x00, 0x00, 0x00, 0x27, 0x06, 0x00, 0x00,
                             0x09, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xfc, 0xff,
                             0xfd, 0xff, 0x07, 0x00, 0x07, 0x49, 0x00, 0x00, 0xe5, 0xf9,
                             0xa5, 0xa5, 0xc0])
    
    # Create debug log file
    if not os.path.exists("test/log"):
        os.makedirs("test/log")
    log = logging.getLogger('minxss_parser_debug')
    handler = logging.FileHandler('test/log/minxss_parser.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    # Run test
    minxss_parser = Minxss_Parser(exampleData, log)
    minxss_parser.testParsePacket(exampleData, log)

