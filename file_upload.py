"""Upload data to the MinXSS team"""
__authors__ = "James Paul Mason"
__contact__ = "jmason86@gmail.com"

import os
import requests


def upload(filename, log):
    url = 'http://lasp.colorado.edu/minxss/beacon/fileupload.php'

    file_to_send = {'filename': (filename, open(filename, 'rb'))}
    if os.path.getsize(filename) > 0:
        r = requests.post(url, files=file_to_send)
        log.info('Uploading data to MinXSS team.')
        log.info(r.text)
    else:
        log.info('Not uploading because data file is empty.')
