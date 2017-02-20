"""Handle serial interface"""
__authors__ = "Colden Rouleau, James Paul Mason"
__contact__ = "jmason86@gmail.com"

import sys
import time
import serial

class connect_serial_decode_kiss():
    def __init__(self, port, baudRate, log):
        self.port = port
        self.baudRate = baudRate
        self.log = log
        self.log.info("Opening port: {0}".format(port))
        self.ser = serial.Serial(port, baudRate, timeout=.01)
        self.ser.flushInput()

        if (not self.ser.readable()):
            raise Exception("Port not readable")

        if (not self.ser.writable()):
            raise Exception("Port not writable")

        #class vars
        self.serial_read_storage = []

    def close(self):
        self.log.info("Closing ground station link")
        self.ser.close

    def read(self):
        data = []
        newdata = []
        while(1):
            newdata = self.ser.read(self.ser.in_waiting)
            for byte in newdata:
                data.append(byte)

            if(self.ser.in_waiting == 0):
                break
        return data

    def testRead(self):
        self.log.info("Testing read on port: {0}".format(self.port))
        portReadable = self.ser.readable()

        if portReadable:
            self.log.info("Test read on port was successful")
        else:
            self.log.error("Test read on port failed")
        return portReadable

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

