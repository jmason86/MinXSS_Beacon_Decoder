"""Handle serial or TCP/IP interfaces and grab MinXSS packet"""
__authors__ = "James Paul Mason"
__contact__ = "jmason86@gmail.com"

import sys
import serial
import socket


class ConnectSerial:
    def __init__(self, port, baud_rate, log):
        self.port = port
        self.baud_rate = baud_rate
        self.log = log

        self.ser = None
        self.start_sync_bytes = None
        self.stop_sync_bytes = None

        self.open_serial_port()

    def open_serial_port(self):
        self.log.info("Opening serial port {0} at baud rate {1}".format(self.port, self.baud_rate))

        self.ser = serial.Serial(self.port, self.baud_rate)
        if not self.ser.readable():
            self.log.error('Serial port not readable.')

    def close(self):
        self.log.info("Closing serial port.")
        self.ser.close()

    def read_packet(self):
        #  From all of the binary coming in, grab and return a single MinXSS packet including all headers/footers
        packet = bytearray()
        buffered_data = bytearray()
        
        found_sync_start_index = 0
        found_sync_stop_index = 0
        while found_sync_start_index == 0 and found_sync_stop_index == 0:
            if self.find_sync_start_index(buffered_data) != -1:
                found_sync_start_index = 1
            if self.find_sync_stop_index(buffered_data) != -1:
                found_sync_stop_index = 1

            buffered_data = self.ser.read()
            for byte in buffered_data:
                packet.append(byte)

            if len(packet) > 500:  # Assuming that there's no way to have this much header on the 254 byte MinXSS packet
                self.log.error("Too many bytes in packet.")
                break
                    
        self.log.info("Packet length [bytes] = " + str(len(packet)))
        return packet

    def find_sync_start_index(self, buffered_serial_data):
        self.set_start_sync_bytes()
        return bytearray(buffered_serial_data).find(self.start_sync_bytes)

    def set_start_sync_bytes(self):
        self.start_sync_bytes = bytearray([0x08, 0x19])

    def find_sync_stop_index(self, buffered_serial_data):
        self.set_stop_sync_bytes()
        return bytearray(buffered_serial_data).find(self.stop_sync_bytes)

    def set_stop_sync_bytes(self):
        self.stop_sync_bytes = bytearray([0xa5, 0xa5])

    def test_read(self):
        self.log.info("Testing read on port: {0}".format(self.port))
        port_readable = self.ser.readable()

        if port_readable:
            self.log.info("Test read on port was successful.")
        else:
            self.log.error("Test read on port failed.")
        return port_readable


class ConnectSocket:
    def __init__(self, ip_address, port, log):
        self.ip_address = ip_address
        self.port = port
        self.log = log
        self.port_readable = None

    def connect_to_port(self):
        self.log.info("Opening IP address: {0} on port: {1}".format(self.ip_address, self.port))

        self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.clientsocket.connect((self.ip_address, int(self.port)))
            self.log.info('Successful port open.')
            self.port_readable = True
        except socket.error as error:
            self.log.warning("Failed connecting to {0} on port {1}".format(self.ip_address, self.port))
            self.log.warning(error)
            self.port_readable = False
        finally:
            return self
    
    def close(self):
        self.log.info("Closing ground station link.")
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
        foundLogPacket = 0
        while((foundSyncStartIndex + foundSyncStopIndex) < 2):
            bufferedData = bytearray(self.clientsocket.recv(1))
            for byte in bufferedData:
                packet.append(byte)
            
            if self.findLogSyncStartIndex(packet) != -1:
                foundLogPacket = 1
            if self.findSyncStartIndex(packet) != -1:
                foundSyncStartIndex = 1
            if self.findSyncStopIndex(packet) != -1:  # once at len(packet) > e.g., 64 then check for sync
                if foundLogPacket == 1:
                    self.log.info("Found log message. Ignoring in search of housekeeping packet.")
                    packet = bytearray()  # Clear out the packet because its a log message not a housekeeping packet
                else:
                    foundSyncStopIndex = 1
            if foundSyncStartIndex + foundSyncStopIndex == 2:
                if self.findSyncStartIndex(packet) > self.findSyncStopIndex(packet):
                    packet = packet[self.findSyncStartIndex(packet):]
                    foundSyncStopIndex = 0
        
            if len(packet) > 500:  # Assuming that there's no way to have this much header on the 254 byte MinXSS packet
                self.log.error("Too many bytes in packet, resetting packet buffer")
                
                if foundSyncStartIndex:
                    self.log.info("Resetting packet buffer to start at the identified start sync index")
                    packet = packet[self.findSyncStartIndex(packet):]
                else:
                    self.log.info("Resetting packet buffer to null")
                    packet = bytearray()

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

    # Purpose:
    #   Find the start of the MinXSS log packet and return the index within minxssSerialData. Will want to throw out these types of packets
    #   because they don't contain any housekeeping telemetry.
    # Input:
    #   minxssSerialData [bytearray]: The direct output of the python serial line (connect_serial_decode_kiss.read()), or simulated data in that format
    # Output:
    #   logPacketStartIndex [int]: The index within minxssSerialData where the start sync bytes were found. -1 if not found.
    #
    def findLogSyncStartIndex(self, minxssSerialData):
        syncBytes = bytearray([0x08, 0x1D])
        logPacketStartIndex = bytearray(minxssSerialData).find(syncBytes)
        return logPacketStartIndex

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
