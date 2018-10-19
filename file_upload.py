"""Upload data to the MinXSS team"""
__authors__ = "James Paul Mason"
__contact__ = "jmason86@gmail.com"

import os
import requests
from logger import Logger


def upload(filename):
    log = Logger().create_log()
    url = 'http://lasp.colorado.edu/minxss/beacon/fileupload.php'

    filename = ensure_slashes_compliant_with_server(filename)

    file_to_send = {'filename': (filename, open(filename, 'rb'))}
    if os.path.getsize(filename) > 0:
        r = requests.post(url, files=file_to_send)
        print(r.text)
        if r.status_code == 200:
            log.info('Successfully uploaded data to MinXSS team.')
            log.info(r.text)
        else:
            log.error('Failed to upload data to MinXSS team. Requests error {}'.format(r.status_code))
    else:
        log.info('Not uploading because data file is empty.')


def ensure_slashes_compliant_with_server(filename):
    return filename.replace('\\', '/')
