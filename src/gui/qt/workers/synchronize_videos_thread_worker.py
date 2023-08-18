import logging
logger = logging.getLogger(__name__)
from pathlib import Path
import threading

from PyQt6.QtCore import pyqtSignal, QThread

from skelly_synchronize.skelly_synchronize import synchronize_videos_from_audio

class SynchronizeVideosThreadWorker(QThread):
    finished = pyqtSignal()
    in_progress = pyqtSignal(str)

    def __init__(
        self,
        input_folder_path: Path,
        synchronized_video_folder_path: Path,
        kill_thread_event: threading.Event
    ):
        super.__init__()
        logger.info("Initializing Synchronize Videos Thread Worker")
        self._kill_thread_event = kill_thread_event
        self._input_folder_path = input_folder_path
        self._syncronzied_video_folder_path = synchronized_video_folder_path
        self._output_folder_path: Path = None
        self._work_done: bool = False

    @property
    def work_done(self) -> bool:
        return self._work_done
    
    @property
    def output_folder_path(self) -> Path:
        return self._output_folder_path
    
    def emit_in_progress_data(self, message:str):
        self.in_progress.emit(message)

    def run(self):
        logger.info("Beginning Synchronize Videos Thread Worker")
        try:
            self._output_folder_path = synchronize_videos_from_audio(
                raw_video_folder_path=self._input_folder_path,
                synchronized_video_folder_path=self._syncronzied_video_folder_path,
                create_debug_plots_bool=True
            )
        except Exception as e:
            logger.exception("Something went wrong while synchronizing videos")
            logger.exception(e)

        
        self.finished.emit()
        self._work_done = True

        logger.info("Finished Synchronize Videos Thread Worker")


