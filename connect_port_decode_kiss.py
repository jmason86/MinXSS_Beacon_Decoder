"""Handle serial or TCP/IP interfaces and KISS decoding"""
__authors__ = "James Paul Mason, Colden Rouleau"
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
    # TODO:
    #   Pull this function out to a separate class that can be called with serial or socket input
    def read_packet(self):
        packet = bytearray()
        syncStartOffset = -1
        while(1):
#            if len(packet) > 0:
#                print len(packet)
#            syncStartOffset = self.findSyncStartIndex(packet)
#            syncStopOffset = self.findSyncStopIndex(packet)
#            
#            # Haven't found start and haven't found stop sync so buffer everything
#            if syncStartOffset == -1 and syncStopOffset == -1:
#                self.log.info("Have not found start and have not found stop")
#                bufferedData = self.ser.read()
#                if len(bufferedData) > 0:
#                    print len(bufferedData)
#                for byte in bufferedData:
#                    packet.append(byte)
#            # Found start sync but haven't found stop sync so buffer everything
#            elif syncStartOffset != -1 and syncStopOffset == -1:
#                self.log.info("Found start but have not found stop")
#                bufferedData = self.ser.read()
#                for byte in bufferedData:
#                    packet.append(byte)
#            # Found start sync and stop sync so truncate packet to within start and stop syncs and break loop
#            elif syncStartOffset != -1 and syncStopOffset != -1:
#                self.log.info("Have found start and have found stop. Woo!")
#                packet = packet[syncStartOffset:syncStopOffset] # Destructively throws out any surrounding partial packets
#                break
#            # Haven't found start sync but have found stop sync so must have missed beginning of packet -- buffer everything
#            elif syncStartOffset == -1 and syncStopOffset != -1:
#                self.log.info("Have not found start but have found stop")
#                bufferedData = self.ser.read()
#                for byte in bufferedData:
#                    packet.append(byte)

            if syncStartOffset == -1 or len(packet[syncStartOffset:]) < 256:
                bufferedData = self.ser.read()
                for byte in bufferedData:
                    packet.append(byte)
            else:
                break
        
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

def testReadMain(port, baudRate, log):
    log.info("Opening port: {0}".format(port))
    ser = serial.Serial(port, baudRate)

    if (not ser.readable()):
        raise Exception("Port not readable")

    log.info("Finished checking serial line readability, closing: {0}".format(port))
    ser.close

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
    # TODO:
    #   Pull this function out to a separate class that can be called with serial or socket input
    def read_packet(self):
        packet = bytearray()
        syncStartOffset = -1
        while(1):
            syncStartOffset = self.findSyncStartIndex(packet)

            if syncStartOffset == -1 or len(packet[syncStartOffset:]) < 254:
                bufferedData = bytearray(self.clientsocket.recv(254))
                print binascii.hexlify(bufferedData)
                for byte in bufferedData:
                    packet.append(byte)
            else:
                break
        
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

class unkiss():
    def __init__(self, packet, log):
        self.packet = packet
        self.log = log

    #Take an arbitrary numeric data array and figure out if it is not a KISS packet, a partial KISS packet, or a full KISS packet
    #returns a control value and the packet (is_ready,[packet],[remaining_data])
    #is_ready=0 means a partial or empty packet (and returns the packet unmodified)
    #is_ready=-1 means an error occurred and the data should be tossed (returns an empty array)
    #is_ready=1 means the packet is ready
    def KISS_read(self,data):
        FRAME_END = 0xC0
        FRAME_ESC = 0xDB
        DATA_FRAME_CODE = 0x00
        TRANSPOSE_FRAME_END = 0xDC
        TRANSPOSE_FRAME_ESC = 0xDD
        FRAME_END_DATA = [FRAME_ESC,TRANSPOSE_FRAME_END]
        FRAME_ESC_DATA = [FRAME_ESC,TRANSPOSE_FRAME_ESC]
        #deal with any frame ends or frame escapes in the data
        i=0
        
        error = 0
        
        #can get fed an empty array and that's OK - just return an empty array, and "remaining_data" is all the data
        if(len(data) == 0):
            return [0,[],data]
        
        if(data[0] != FRAME_END):
            self.log.error("KISS_read received a packet that did not start with a FRAME_END byte (0xC0)! Please toss data!")
            error = 1
        
        #if we have a FRAME_END byte but nothing else, just return and wait for more data
        if(error==0 and len(data)<2):
            return [0,[],data]
        
        
        if(error==0 and data[1] != DATA_FRAME_CODE):
            self.log.error("KISS_read received a packet with where the 2nd byte was not DATA_FRAME_CODE (0x00). Cannot process, please toss data.")
            error = 1
        
        i = 2
        pkt_ind = 0
        packet = []
        while(error==0):
            #if don't have enough data to process, return
            if(len(data) <= i):
                return [0,[],data]
            if(data[i] == FRAME_ESC):
                i += 1 #the escaped char takes two
                #make sure we still have something to look at
                if(len(data)>i):
                    if(data[i] == TRANSPOSE_FRAME_ESC):
                        packet.append(FRAME_ESC)
                    elif(data[i] == TRANSPOSE_FRAME_END):
                        packet.append(FRAME_END)
                    else:
                        self.log.error("KISS_read saw FRAME_ESC that was not followed by either TRANSPOSE. Toss packet! (see packet printout)")
                        error = 1
                        break;
                else:
                    #we have a partial packet (since it ends with FRAME_ESC) - which is fine, we'll come back later
                    return(0,[],data)
        
            #check to see if we're done
            elif(data[i] == FRAME_END):
                #make sure we don't have an empty packet
                if(len(packet)>0):
                    #if we're good, return the packet and the unprocessed data
                    return(1, packet, data[i+1:])
                else:
                    self.log.error("Received an empty packet! Consisted only of KISS control bytes!")
                    error = 1
                    break;
        else:
            packet.append(data[i])
            i += 1
            
            if(error):
                self.log.error("KISS_read: Bytes: ")
                for byte in data:
                    self.log.error(byte)
                return [-1,[],[]]
            else:
                self.log.error("CODE ERROR in KISS_read! While Loop finished without an error, and did not return!")
                return [-1,[],[]]


if __name__ == '__main__':
    if (len(sys.argv) < 4):
        raise Exception("Must pass in port name (string), baud rate (integer), and python log reference")
    else:
        testReadMain(sys.argv[1], sys.argv[2], sys.argv[3])

