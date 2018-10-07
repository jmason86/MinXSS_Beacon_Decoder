import logging
import os
from connect_port_get_packet import ConnectSocket


class TestPort:
    def create_log(self):
        self.ensure_log_folder_exists()
        self.log = logging.getLogger('minxss_beacon_decoder_debug')
        handler = logging.FileHandler(self.create_log_filename())
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        self.log.addHandler(handler)
        self.log.setLevel(logging.DEBUG)

    @staticmethod
    def ensure_log_folder_exists():
        if not os.path.exists(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "log")):
            os.makedirs(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "log"))

    @staticmethod
    def create_log_filename():
        return os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "log", "minxss_beacon_decoder_debug.log")

    def test_socket(self):
        # Make sure test_send_tcpip_packets is running in a terminal window first
        self.create_log()

        self.invalid_port_fails()
        self.valid_port_connects()
        self.can_read_packet()

    def invalid_port_fails(self):
        connect_socket = ConnectSocket(ip_address='localhost', port='10001', log=self.log)
        connected_port = connect_socket.connect_to_port()
        assert connected_port.port_readable is False

    def valid_port_connects(self):
        connect_socket = ConnectSocket('localhost', '10006', self.log)
        self.connected_port = connect_socket.connect_to_port()
        assert self.connected_port.port_readable

    def can_read_packet(self):
        packet = self.connected_port.read_packet()
        assert len(packet) == 272
