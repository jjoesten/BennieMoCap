import logging
logger = logging.getLogger(__name__)

import threading
from pathlib import Path
from typing import Union

from PyQt6.QtCore import pyqtSignal, QThread

from src.core_processes.capture_volume_calibration.charuco.charuco_board_definition import CharucoBoardDefinition
from src.core_processes.capture_volume_calibration.run_anipose_capture_volume_calibration import run_anipose_capture_volume_calibration

class AniposeCalibrationThreadWorker(QThread):
    finished = pyqtSignal()
    in_progress = pyqtSignal(str)

    def __init__(
        self,
        calibration_videos_folder_path: Union[str, Path],
        charuco_square_size: Union[int, float],
        kill_thread_event: threading.Event,
        charuco_board_definition: CharucoBoardDefinition = None,
    ):
        super().__init__()
        logger.info(f"Initilizing Anipose Calibration Thread Worker for videos in path {calibration_videos_folder_path}")

        if charuco_board_definition is None:
            charuco_board_definition = CharucoBoardDefinition()

        self._kill_thread_event = kill_thread_event
        self._charuco_board_definition = charuco_board_definition
        self._charuco_square_size = charuco_square_size
        self._calibration_videos_folder_path = calibration_videos_folder_path

        self._work_done = False

    @property
    def work_done(self) -> bool:
        return self._work_done
    
    def _emit_in_progress_data(self, message: str):
        self.in_progress.emit(message)
    
    def run(self):
        logger.info(f"Beginning Anipose Calibration with charuco square size (mm): {self._charuco_square_size}")

        try:
            run_anipose_capture_volume_calibration(
                charuco_board_definition = self._charuco_board_definition,
                charuco_square_size = self._charuco_square_size,
                calibration_videos_folder_path = self._calibration_videos_folder_path,
                pin_camera_0_to_origin = True,
                progress_callback=self._emit_in_progress_data,
            )
        except Exception as e:
            logger.exception("Something went wrong durion anipose calibration")
            logger.exception(e)

        self.finished.emit()
        self._work_done = True

        logger.info("Anipose Calibration Complete")