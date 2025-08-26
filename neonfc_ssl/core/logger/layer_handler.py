import logging

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from multiprocessing.queues import Queue


class LayerHandler(logging.Handler):
    def __init__(self, queue: 'Queue'):
        super().__init__()
        self.queue= queue

    def emit(self, record):
        try:
            self.queue.put(record)
        except Exception:
            self.handleError(record)
