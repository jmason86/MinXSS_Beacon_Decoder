import logging
import os


class Logger:
    def __init__(self):
        self.create_log()

    def create_log(self):
        """
        For debugging and informational purposes.
        """
        self.ensure_log_folder_exists()
        log = logging.getLogger('minxss_beacon_decoder_debug')
        handler = logging.FileHandler(self.create_log_filename())
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)
        return log

    @staticmethod
    def ensure_log_folder_exists():
        if not os.path.exists(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "log")):
            os.makedirs(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "log"))

    @staticmethod
    def create_log_filename():
        return os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "log", "minxss_beacon_decoder_debug.log")
