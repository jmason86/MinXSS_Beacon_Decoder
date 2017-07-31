"""Upload data to the MinXSS team"""
__authors__ = "James Paul Mason"
__contact__ = "jmason86@gmail.com"

import requests

def upload(filename, log):
    # Server settings
    url = 'http://lasp.colorado.edu/minxss/beacon/fileupload.php'
    
    # Access the file
    fileToSend = {'filename': (filename, open(filename, 'rb'))}

    # Send the file
    r = requests.post(url, files = fileToSend)

    log.info(r.text)
