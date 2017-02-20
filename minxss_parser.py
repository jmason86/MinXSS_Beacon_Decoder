# Warning: this program is executed in Python 2, because the
# serial to TCP program is run using the "python" command.
# (even though it might look like Python 3)

import struct
import numpy as np

ENCODING = 'utf-8'


def fletcher16(data, offset=0, length=None):
    """Do a fletcher check on data."""
    if length is None:
        length = len(data)
    sum1 = 255
    sum2 = 255
    while length > 0:
        tlen = 21 if length > 21 else length
        length -= tlen
        while True:
            temp = data[offset] & 0xFF
            offset += 1
            sum1 += temp
            sum2 += sum1
            tlen -= 1
            if tlen <= 0:
                break
        sum1 = (sum1 & 0xFF) + (sum1 >> 8)
        sum2 = (sum2 & 0xFF) + (sum2 >> 8)
    sum1 = (sum1 & 0xFF) + (sum1 >> 8)
    sum2 = (sum2 & 0xFF) + (sum2 >> 8)
    return sum1 & 0xFF, sum2 & 0xFF


def decode(integers):
    """Convert an array of integers into a string by the integers corresponding unicode value."""
    string = ''
    for integer in integers:
        string += chr(integer)
    return string


def get_bit(array, index):
    """Get an individual bit from a bytearray (which could be a single byte)."""
    return (array[index // 8] >> ((7-index) % 8)) & 1


def set_bit(array, index, bit):
    """Set an individual bit inside a bytearray (which could be a single byte)."""
    if get_bit(array, index) != bit:
        array[index // 8] ^= 1 << ((7-index) % 8)


def hbytes(full_message):
    """Convert the received binary message into hex."""
    numlist = list(full_message)
    for i in range(len(numlist)):
        numlist[i] = hex(numlist[i])[2:]
        numlist[i] = numlist[i].zfill(2)
    numlist = ''.join(numlist).upper()
    return '0x' + numlist


def bbytes(full_message):
    """Convert the received binary message into a bytearray. Not actually called by anything."""
    numlist = list(full_message)
    for i in range(len(numlist)):
        numlist[i] = bin(numlist[i])[2:]
        numlist[i] = numlist[i].zfill(8)
    numlist = ''.join(numlist).upper()
    return '0b' + numlist


class MinxssParser:
    
    def __init__(self):
        self.buffer = bytearray()
        self.reading_message = False

    def received_data(self, data):
        """Pass each string character of data to received_char function."""
        for char in data:
            self.received_char(char)

    def received_char(self, char):
        """Convert char to integer and store in the instance variable: buffer, which is a bytearray."""
        self.buffer.append(ord(char))
        if not self.reading_message:
            if len(self.buffer) == 4:
                # TODO: Change these 4 alignment bytes to the fiducial used on MinXSS (see minxss_read_packets.pro)
                if self.buffer[0] == 0xDE and self.buffer[1] == 0xAD and \
                   self.buffer[2] == 0xBE and self.buffer[3] == 0xEF:
                       self.buffer = self.buffer[4:]
                       self.reading_message = True
                       print('Received alignment bytes. Listening for message...')
                else:
                    self.buffer = self.buffer[1:]
    
    def received_hex_string(self, hex_string):
        """Clears buffer, passes each string character to received_char function. Not actually called by anything."""
        self.buffer = bytearray()
        self.reading_message = True
        for i in range(len(hex_string)//2):
            self.received_char(chr(int(hex_string[2*i:2*i+2], 16)))
    
    def message_is_complete(self):  # Gets called from tcp_serial_redirect
        """Returns true if the buffer has >= 232 bytes"""
        return len(self.buffer) >= 232  # TODO: Change to the length expected for MinXSS

    def get_message(self):  # Gets called from tcp_serial_redirect
        """Parses some key data, reformats it, replaces it in the received data, adds headers and checksums, and returns the result"""
        original, temp = self.buffer[:232], self.buffer[232:] # JPM: Fancy python syntax for setting two variables in one line

        # JPM: QB50 noted the octet stuff is necessary for the gs client
        # TODO: I'll need to isolate some bytes and not bother interpreting the interim bytes
        # Insert spacing; before every 1-bit flag set we need 7 additional
        # bits to make the fields line up with the octets.
        message = bytearray(len(original) + 28)
        offset = 0
        for i in range(len(original)*8):
            if i >= 32:
                offset = ((i + 25) // 57) * 7
            set_bit(message, i + offset, get_bit(original, i))

        # Replace the seven 1-byte integer fields with 4-byte floating point fields.
        index = 4  # time field # TODO: Replace with the corresponding index of a MinXSS hk packet
        for k in range(32):
            # Read each of the 1-byte fields (as unsigned integers 0-255)
            battery_bus_voltage, battery_bus_current, _3V3_bus_current, _5V_bus_current, \
                                 comm_temperature, eps_temperature, battery_temperature = \
                                 message[index+1], message[index+2], message[index+3], \
                                 message[index+4], message[index+5], message[index+6], \
                                 message[index+7] # JPM: Another fancy python multi-set, TODO: replace with MinXSS selected telemetry 
            # Apply formulas to pretty them up (they are now floating-point)
            # TODO: Replace with MinXSS formulas
            battery_bus_voltage = (battery_bus_voltage + 60.0) / 20
            battery_bus_current = (battery_bus_current - 127.0) / 127
            _3V3_bus_current /= 40.0
            _5V_bus_current /= 40.0
            comm_temperature = (comm_temperature - 60.0) / 4
            eps_temperature = (eps_temperature - 60.0) / 4
            battery_temperature = (battery_temperature - 60.0) / 4
            array = (battery_bus_voltage, battery_bus_current, _3V3_bus_current, _5V_bus_current,
                     comm_temperature, eps_temperature, battery_temperature)
            # Replace 1-byte fields with decoded floats
            # TODO: Figure out why this decoding is necessary at all for the message if it just gets forwarded not displayed
            for j in range(7): #JPM: This is 7 likely because there are 7 telemetry items extracted
                i = index+1+j*4
                message = message[:i] + struct.pack('f', array[j]) + message[i+1:]
            # Length of one data set, after adding floats
            index += 1+4*7
        
        # 0x000000000000000000000000000000000000
        kiss_header = bytearray((0x00,)) * 18
        # 0xABCD0000000003[message-length]00[checksum]
        length = (len(message) +
                  11 +  # header & checksum A
                  6)  # checksum B & hmac
        rax_header = bytearray((0xAB, 0xCD, 0x00, 0x00,
                                0x00, 0x00, 0x03, length & 0xFF,
                                (length >> 8) & 0xFF)) # JPM: this seems to be creating a custom message to be forwarded, containing the message length, was that necessary for something?
        checksum_a = bytearray(fletcher16(rax_header))
        checksum_b = bytearray(fletcher16(message))
        # 0x00000000
        hmac = bytearray((0x00,)) * 4 # JPM: No idea why this is here... necessary fixed length padding?
        full_message = kiss_header + rax_header + checksum_a + message + checksum_b + hmac
        # Possibly we have received one and a half messages, we would like
        # to be able to detect the second one instead of discarding it.
        # This shouldn't be necessary, of course, since get_message should
        # be called as soon as message_is_complete() returns True.
        self.buffer = bytearray() # JPM: Clears buffer
        self.reading_message = False # JPM: Deconflict 
        self.received_data(decode(temp)) # JPM: If a partial message came in after the just finished full message, stick that back in the buffer

        print('Sending message: ' + hbytes(full_message))
        
        return decode(full_message)
