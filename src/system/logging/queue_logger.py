from logging import LogRecord
import multiprocessing
from logging.handlers import QueueHandler

class DirectQueueHandler(QueueHandler):
    def __init__(self, queue: multiprocessing.Queue):
        super().__init__(queue)

    def enqueue(self, record: LogRecord) -> None:
        self.queue.put(record)