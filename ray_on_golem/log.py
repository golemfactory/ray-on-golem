import gzip
import os
import shutil
from logging.handlers import RotatingFileHandler

GZIP_EXTENSION = ".gz"


class ZippingRotatingFileHandler(RotatingFileHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # rollover on start, to ensure that a new logfile is initialized with each new logger
        # unless we're starting for the very first time
        if self.stream.tell():
            self.doRollover()

    @staticmethod
    def namer(default_name: str):
        default_name += GZIP_EXTENSION
        return default_name

    @staticmethod
    def rotator(source: str, dest: str):
        if os.path.exists(source):
            with open(source, "rb") as source_f:
                with gzip.open(dest, "wb") as dest_f:
                    shutil.copyfileobj(source_f, dest_f)
            os.remove(source)
