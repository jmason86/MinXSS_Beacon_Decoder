from connect_port_get_packet import ConnectSocket


class TestPort:
    def test_socket(self):
        # Make sure test_send_tcpip_packets is running in a terminal window first
        self.invalid_port_fails()
        self.valid_port_connects()
        self.can_read_packet()

    @staticmethod
    def invalid_port_fails():
        connect_socket = ConnectSocket(ip_address='localhost', port='10001')
        connected_port = connect_socket.connect_to_port()
        assert connected_port.port_readable is False

    def valid_port_connects(self):
        connect_socket = ConnectSocket('localhost', '10006')
        self.connected_port = connect_socket.connect_to_port()
        assert self.connected_port.port_readable

    def can_read_packet(self):
        packet = self.connected_port.read_packet()
        assert len(packet) == 272
