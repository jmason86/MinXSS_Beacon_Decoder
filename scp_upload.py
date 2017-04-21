"""Upload data to the MinXSS team"""
__authors__ = "James Paul Mason"
__contact__ = "jmason86@gmail.com"

import paramiko
from scp import SCPClient

def upload(file):
    # Server settings
    ip = "73.217.122.64" # Current IP for James's Mac Mini, but hasn't yet been made static
    port = 22
    username = "minxssham"
    password = "minxsshampass"
    directory = "Dropbox/minxss_dropbox/data/ham_data/"
    
    # Set up
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, port, username, password)
    scp = SCPClient(ssh.get_transport())
    
    # Do the transfer
    scp.put(file, remote_path = directory)
