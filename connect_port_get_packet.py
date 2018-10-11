"""Handle serial or TCP/IP interfaces and grab spacecraft packet packet"""
__authors__ = "James Paul Mason"
__contact__ = "jmason86@gmail.com"

import serial
import socket
from find_sync_bytes import FindSyncBytes


class PacketReader:
    def __init__(self):
        self.fsb = FindSyncBytes()

    def read_packet(self):
        #  From all of the binary coming in, grab and return a single packet including all headers/footers
        packet = bytearray()

        found_sync_start_index = 0
        found_sync_stop_index = 0
        found_log_packet = 0
        while (found_sync_start_index + found_sync_stop_index) < 2:
            buffered_data = self.get_data_from_buffer()
            for byte in buffered_data:
                packet.append(byte)

            if self.fsb.find_log_sync_start_index(packet) != -1:
                found_log_packet = True
            if self.fsb.find_sync_start_index(packet) != -1:
                found_sync_start_index = True
            if self.fsb.find_sync_stop_index(packet) != -1:
                if found_log_packet:
                    packet = bytearray()  # Clear out the packet because its a log message not a housekeeping packet
                else:
                    found_sync_stop_index = True
            if found_sync_start_index and found_sync_stop_index:
                if self.fsb.find_sync_start_index(packet) > self.fsb.find_sync_stop_index(packet):
                    packet = packet[self.fsb.find_sync_start_index(packet):]
                    found_sync_stop_index = 0

            if len(packet) > 500:  # Assuming that there's no way to have this much header on the 254 byte MinXSS packet
                if found_sync_start_index:
                    packet = packet[self.fsb.find_sync_start_index(packet):]  # start packet at start sync
                else:
                    packet = bytearray()

        return packet

    @staticmethod
    def get_data_from_buffer():
        # Placeholder method to be overridden by subclasses for serial and sockets
        # because they have different objects to read from and syntax to read with.
        return bytearray()


class ConnectSerial(PacketReader):
    def __init__(self, port, baud_rate, log):
        super(ConnectSerial, self).__init__()

        self.port = port
        self.baud_rate = baud_rate
        self.log = log

        self.ser = None
        self.port_readable = None
        self.start_sync_bytes = None
        self.stop_sync_bytes = None

    def connect_to_port(self):
        self.log.info("Opening serial port {0} at baud rate {1}".format(self.port, self.baud_rate))

        self.ser = serial.Serial(self.port, self.baud_rate)
        if not self.ser.readable():
            self.log.error('Serial port not readable.')
            self.port_readable = False
        else:
            self.log.info('Successful serial port open.')
            self.port_readable = True
            return self

    def get_data_from_buffer(self):
        return bytearray(self.ser.read())

    def close(self):
        self.log.info("Closing serial port.")
        self.ser.close()


class ConnectSocket(PacketReader):
    def __init__(self, ip_address, port, log):
        super(ConnectSocket, self).__init__()

        self.ip_address = ip_address
        self.port = port
        self.log = log

        self.client_socket = None
        self.port_readable = None

    def connect_to_port(self):
        self.log.info("Opening IP address: {0} on port: {1}".format(self.ip_address, self.port))

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.client_socket.connect((self.ip_address, int(self.port)))
            self.log.info('Successful TCP/IP port open.')
            self.port_readable = True
        except socket.error as error:
            self.log.warning("Failed connecting to {0} on port {1}".format(self.ip_address, self.port))
            self.log.warning(''.format(error))
            self.port_readable = False
        finally:
            return self

    def get_data_from_buffer(self):
        return bytearray(self.client_socket.recv(1))
    
    def close(self):
        self.log.info("Closing TCP/IP port.")
        self.client_socket.close()
