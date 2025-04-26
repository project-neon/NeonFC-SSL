import logging
from datetime import datetime
from os.path import join


class BinaryFileHandler(logging.Handler):
    def __init__(self, path, filename):
        super().__init__()
        self.file=open(join(path, f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{filename}"), 'ab')  # append in binary mode

    def emit(self, record):
        try:
            msg = self.format(record)
            length = len(msg).to_bytes(4, byteorder='big')  # prefix with 4-byte length
            self.file.write(length + msg)
            self.file.flush()
        except Exception:
            self.handleError(record)

    def close(self):
        self.file.close()
        super().close()
