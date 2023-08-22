import logging
logger = logging.getLogger(__name__)

import multiprocessing
import time
from pathlib import Path

from PyQt6.QtCore import pyqtSignal, QThread

from src.core_processes.process_motion_capture_videos.process_session_folder import process_session_folder

from src.data_layer.session_models.post_processing_parameter_models import PostProcessingParameterModel
from src.system.paths_and_filenames.folder_and_filenames import SESSION_PARAMETERS_JSON_FILENAME
from src.utilities.dict import save_dictionary_to_json

class ProcessMotionCaptureDataThreadWorker(QThread):
    finished = pyqtSignal()
    in_progress = pyqtSignal(object)

    def __init__(self, post_processing_parameters: PostProcessingParameterModel, kill_event: multiprocessing.Event, parent=None):
        super().__init__()
        self._post_processing_parameters = post_processing_parameters
        self._kill_event = kill_event
        self._queue = multiprocessing.Queue()
        self._process = multiprocessing.Process(target=process_session_folder, args=(self._post_processing_parameters, self._kill_event, self._queue))

    def run(self):
        logger.info(f"Beginning processing of motion capture data with parameters: {self._post_processing_parameters.__dict__}")
        self._kill_event.clear()

        session_info_dict = self._post_processing_parameters.model_dump(exclude={"session_info_model"})
        Path(self._post_processing_parameters.session_info_model.output_data_folder_path).mkdir(exist_ok=True, parents=True)
        
        save_dictionary_to_json(
            save_path=self._post_processing_parameters.session_info_model.output_data_folder_path,
            filename=SESSION_PARAMETERS_JSON_FILENAME,
            dictionary=session_info_dict
        )

        try:
            self._process.start()
            while self._process.is_alive():
                time.sleep(0.01)
                if self._queue.empty():
                    continue
                else:
                    record = self._queue.get()
                    print(f"message: {record.msg}")
                    self.in_progress.emit(record)
            
            while not self._queue.empty():
                record = self._queue.get()
                print(f"message: {record.msg}")
                self.in_progress.emit(record)
        except Exception as e:
            logger.error(f"Error processing motion capture data: {str(e)}")
        
        logger.info("Finished processing session folder")
        
        self.finished.emit()