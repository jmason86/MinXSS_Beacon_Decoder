"""Handle serial or TCP/IP interfaces and grab MinXSS packet"""
__authors__ = "James Paul Mason"
__contact__ = "jmason86@gmail.com"

import sys
import time
import serial
import socket
import pdb, binascii

class connect_serial():
    def __init__(self, port, baudRate, log):
        self.port = port
        self.baudRate = baudRate
        self.log = log
        self.log.info("Opening port: {0}".format(port))
        self.ser = serial.Serial(port, baudRate, timeout=.01)
        #self.ser.flushInput()

        if (not self.ser.readable()):
            raise Exception("Port not readable")

    def close(self):
        self.log.info("Closing ground station link")
        self.ser.close
    
    # Purpose:
    #   From all of the binary coming in, grab a single MinXSS packet
    # Input:
    #   None
    # Output:
    #   packet [bytearray]: A single MinXSS packet with all headers and footers
    def read_packet(self):
        packet = bytearray()
        bufferedData = bytearray()
        
        foundSyncStartIndex = 0
        foundSyncStopIndex = 0
        while(foundSyncStartIndex == 0 and foundSyncStopIndex == 0):
            if self.findSyncStartIndex(bufferedData) != -1:
                foundSyncStartIndex = 1
            if self.findSyncStopIndex(bufferedData) != -1:
                foundSyncStopIndex = 1

            bufferedData = self.ser.read()
            for byte in bufferedData:
                packet.append(byte)

            if len(packet) > 500: # Assuming that there's no way to have this much header on the 254 byte MinXSS packet
                self.log.error("Too many bytes in packet")
                break
                    
        self.log.info("Packet length [bytes] = " + str(len(packet)))
        return packet

# Purpose:
    #   Find the start of the MinXSS packet and return the index within minxssSerialData
    # Input:
    #   minxssSerialData [bytearray]: The direct output of the python serial line (connect_serial_decode_kiss.read()), or simulated data in that format
    # Output:
    #   packetStartIndex [int]: The index within minxssSerialData where the start sync bytes were found. -1 if not found.
    #
    def findSyncStartIndex(self, minxssSerialData):
        syncBytes = bytearray([0x08, 0x19])
        packetStartIndex = bytearray(minxssSerialData).find(syncBytes)
        return packetStartIndex

    # Purpose:
    #   Find the end of the MinXSS packet and return the index within minxssSerialData
    # Input:
    #   minxssSerialData [bytearray]: The direct output of the python serial line (connect_serial_decode_kiss.read()), or simulated data in that format
    # Output:
    #   packetStopIndex [int]: The index within minxssSerialData where the end sync bytes were found. -1 if not found.
    #
    def findSyncStopIndex(self, minxssSerialData):
        syncBytes = bytearray([0xa5, 0xa5])
        packetStopIndex = bytearray(minxssSerialData).find(syncBytes)
        return packetStopIndex

    def testRead(self):
        self.log.info("Testing read on port: {0}".format(self.port))
        portReadable = self.ser.readable()

        if portReadable:
            self.log.info("Test read on port was successful")
        else:
            self.log.error("Test read on port failed")
        return portReadable

class connect_socket():
    def __init__(self, ipAddress, port, log):
        self.ipAddress = ipAddress
        self.port = port
        self.log = log
        self.log.info("Opening IP address: {0} on port: {1}".format(ipAddress, port))

        self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientsocket.connect((ipAddress, int(port)))
    
    def close(self):
        self.log.info("Closing ground station link")
        self.clientsocket.close()
    
    # Purpose:
    #   From all of the binary coming in, grab a single MinXSS packet
    # Input:
    #   None
    # Output:
    #   packet [bytearray]: A single MinXSS packet with all headers and footers
    #
    def read_packet(self):
        packet = bytearray()
        bufferedData = bytearray()
        
        foundSyncStartIndex = 0
        foundSyncStopIndex = 0
        while(foundSyncStartIndex == 0 and foundSyncStopIndex == 0):
            if self.findSyncStartIndex(bufferedData) != -1:
                foundSyncStartIndex = 1
            if self.findSyncStopIndex(bufferedData) != -1:
                foundSyncStopIndex = 1
            
            bufferedData = bytearray(self.clientsocket.recv(256))
            for byte in bufferedData:
                packet.append(byte)
    
            if len(packet) > 500: # Assuming that there's no way to have this much header on the 254 byte MinXSS packet
                self.log.error("Too many bytes in packet")
                break
    
        self.log.info("Packet length [bytes] = " + str(len(packet)))
        return packet
    
    # Purpose:
    #   Find the start of the MinXSS packet and return the index within minxssSerialData
    # Input:
    #   minxssSerialData [bytearray]: The direct output of the python serial line (connect_serial_decode_kiss.read()), or simulated data in that format
    # Output:
    #   packetStartIndex [int]: The index within minxssSerialData where the start sync bytes were found. -1 if not found.
    #
    def findSyncStartIndex(self, minxssSerialData):
        syncBytes = bytearray([0x08, 0x19]) # Other Cubesats: Change these start sync bytes to whatever you are using to define the start of your packet
        packetStartIndex = bytearray(minxssSerialData).find(syncBytes)
        return packetStartIndex

    # Purpose:
    #   Find the end of the MinXSS packet and return the index within minxssSerialData
    # Input:
    #   minxssSerialData [bytearray]: The direct output of the python serial line (connect_serial_decode_kiss.read()), or simulated data in that format
    # Output:
    #   packetStopIndex [int]: The index within minxssSerialData where the end sync bytes were found. -1 if not found.
    #
    def findSyncStopIndex(self, minxssSerialData):
        syncBytes = bytearray([0xa5, 0xa5]) # Other CubeSats: Change these stop sync bytes to whatever you are using to define the end of your packet
        packetStopIndex = bytearray(minxssSerialData).find(syncBytes)
        return packetStopIndex

def testReadMain(port, baudRate, log):
    log.info("Opening port: {0}".format(port))
    ser = serial.Serial(port, baudRate)
    
    if (not ser.readable()):
        raise Exception("Port not readable")
    
    log.info("Finished checking serial line readability, closing: {0}".format(port))
    ser.close

if __name__ == '__main__':
    if (len(sys.argv) < 4):
        raise Exception("Must pass in port name (string), baud rate (integer), and python log reference")
    else:
        testReadMain(sys.argv[1], sys.argv[2], sys.argv[3])
