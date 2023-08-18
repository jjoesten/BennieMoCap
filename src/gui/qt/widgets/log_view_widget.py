import logging
from logging.handlers import QueueHandler
logger = logging.getLogger(__name__)

import multiprocessing
import threading
from queue import Queue

from PyQt6 import QtCore
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QApplication, QPlainTextEdit

from src.gui.qt.utilities.colors import get_next_color, rgb_color_generator
from src.system.logging.configure import log_view_format_string

log_view_formatter = logging.Formatter(fmt=log_view_format_string, datefmt="%Y-%m-%dT%H:%M:%S")

level_colors = {
    "DEBUG": (169, 169, 169), #gray
    "INFO": (255, 255, 255), #white
    "WARNING": (255, 165, 0), #orange
    "ERROR": (255, 0, 0), #red
}

process_colors = {}
thread_colors = {}
code_path_colors = {}

class LoggingQueueListener(QThread):
    log_message_signal = QtCore.pyqtSignal(object)

    def __init__(self, queue: Queue, exit_event: threading.Event(), parent=None):
        super().__init__(parent)
        self._queue = queue
        self._exit_event = exit_event

    def run(self):
        logger.info("Starting LoggingQueueListener thread")
        try:
            while not self._exit_event.is_set():
                if self._queue.empty():
                    continue

                record = self._queue.get(block=True)
                if record is None:
                    break

                self.log_message_signal.emit(record)
        except Exception as e:
            logger.exception(e)
            self.close()
    
    def close(self):
        logger.info("Exiting LoggingQueueListener thread")
        self._exit_event.set()

class LogViewWidget(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setReadOnly(True)

        self._queue = multiprocessing.Queue(-1)
        self._queue_handler = QueueHandler(self._queue)
        self._queue_handler.setFormatter(log_view_formatter)
        logging.getLogger("").handlers.append(self._queue_handler)

        self._exit_event = threading.Event()
        self._queue_listener = LoggingQueueListener(queue=self._queue, exit_event=self._exit_event)
        self._queue_listener.log_message_signal.connect(self.add_log)
        self.timestamp_color_gen = rgb_color_generator((50,255,255), (255, 50, 255), phase_increment=0.2)
        self.log_message_color_gen = rgb_color_generator((128,255,100), (100, 255, 255), phase_increment=0.7)
        self.show_colors = True
        self.show_code_path_info = True
        self._queue_listener.start()

    def add_log(self, record: logging.LogRecord):
        level =  record.levelname.ljust(7)
        timestamp = f"[{record.asctime}.{record.msecs:04.0f}]".ljust(24)
        process_id = f"{record.process}".rjust(6)
        thread_id = f"{record.thread}".rjust(6)
        full_message = record.getMessage().split(":::::")[-1].strip()
        message_content = full_message.split("||||")[-1].strip()
        code_path = full_message.split("||||")[0].strip()
        package, method, line = code_path.split(":")

        r,g,b = level_colors.get(level.strip(), (255, 255, 255))
        level_color = f"<span style='color:rgb({r},{g},{b});'>{level}</span>"

        r,g,b = next(self.timestamp_color_gen)
        timestamp_color = f"<span style='color:rgb({r},{g},{b});'>{timestamp}</span>"

        if process_id not in process_colors:
            process_colors[process_id] = get_next_color()
        r,g,b = process_colors[process_id]
        process_str = f"ProcessID:{process_id}"
        process_id_color = f"<span style='color:rgb({r},{g},{b});'>{process_str}</span>"

        thread_process_id_str = f"{thread_id}:{process_id}"
        if thread_process_id_str not in thread_colors:
            thread_colors[thread_process_id_str] = get_next_color()
        r,g,b = thread_colors[thread_process_id_str]
        thread_str = f"ThreadID:{thread_id}"
        thread_id_color = f"<span style='color:rgb({r},{g},{b});'>{thread_str}</span>"

        process_id_thread_id_color = f"{process_id_color} {thread_id_color}"
        process_id_thread_id_color.ljust(25)

        if package + method not in code_path_colors:
            code_path_colors[package + method] = get_next_color()
        r,g,b = code_path_colors[package + method]
        code_path_color = f"<span style='color:rgb({r},{g},{b});'>{code_path}</span>"

        r,g,b = (255, 255, 255)
        message_color = f"<span style='color:rgb({r},{g},{b});'>{message_content}</span>"

        colored_log_entry = f"{timestamp_color}[{level_color}] {process_id_thread_id_color} {code_path_color} ::: {message_color}"
        self.appendHtml(colored_log_entry)

    def closeEvent(self, event):
        logger.info("Exiting LogViewWidget")
        self._exit_event.set()
        self._queue_listener.close()
        logging.getLogger("").handlers.remove(self._queue_handler)
        super().closeEvent(event)
                