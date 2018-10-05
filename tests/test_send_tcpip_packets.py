# 1. Run this code in a dedicated terminal
# 2. Launch the beacon decoder and connect it to ip = localhost, port = (see hard-code value below)
# 3. Observe that the sequence of data are decoded and red/yellow/green highlighted

import socket
import time
from example_data import get_example_data

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 10006
server_socket.bind(('localhost', port))
server_socket.listen(5)  # become a server socket, maximum 5 connections
print('Ready for client connections on port {}.'.format(port))

# Infinite loop waiting for client connection
test_in_progress = True
while test_in_progress:
    connection, address = server_socket.accept()
    for i in range(0, 7):
        connection.send(get_example_data(i))
        print('Sent example packet data number {}'.format(i))
        time.sleep(3)  # Nominal beacon cadence is actually 9 seconds
        if i == 6:
            print('Test complete.')
            test_in_progress = False
