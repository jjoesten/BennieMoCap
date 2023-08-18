import logging
logger = logging.getLogger(__name__)

import debugpy

import threading
from pathlib import Path
from shutil import copyfile

from PyQt6.QtCore import pyqtSignal, QThread

# from skelly_synchronize.skelly_synchronize import create_video_info_dict, get_fps_list

from src.system.paths_and_filenames.folder_and_filenames import SYNCHRONIZED_VIDEOS_FOLDER_NAME
from src.utilities.video import get_video_paths, create_video_info_dict, get_fps_list, change_framerate_ffmpeg

class MatchFramerateThreadWorker(QThread):
    finished = pyqtSignal()
    in_progress = pyqtSignal(str)

    def __init__(
        self,
        input_folder_path: Path,
        output_folder_path: Path,
        kill_thread_event: threading.Event
    ):
        super().__init__()
        logger.info("Initializing Match Framerate Thread Worker")
        self._kill_thread_event = kill_thread_event
        self._input_folder_path = input_folder_path
        self._output_folder_path = output_folder_path
        self._return_folder_path = None
        self._work_done = False

    @property
    def work_done(self):
        return self._work_done

    @property
    def output_folder_path(self) -> Path:
        return self._return_folder_path
    
    def _emit_in_progress_data(self, message: str):
        self.in_progress.emit(message)

    def run(self):
        logger.info("Beginning Match Framerate Thread Worker")
        debugpy.debug_this_thread()
        try:
            self._return_folder_path = self._match_framerate()
        except Exception as e:
            logger.exception("Something went wrong while matching framerate of videos")
            logger.exception(e)

        self.finished.emit()
        self._work_done = True

        logger.info("Match Framerate Threadworker Finished")

    def _match_framerate(self):
        debugpy.debug_this_thread()
        video_file_list = get_video_paths(self._input_folder_path)
        video_info_dict = create_video_info_dict(video_filepath_list=video_file_list)
        fps_list = get_fps_list(video_info_dict=video_info_dict)

        min_fps = min(fps_list)

        for key in video_info_dict:
            video_info = video_info_dict[key]
            input_path = Path(video_info["video_pathstring"])
            output_filename = f"fr_{input_path.name}"
            output_path = self._output_folder_path / SYNCHRONIZED_VIDEOS_FOLDER_NAME / output_filename

            if video_info["video_fps"] > min_fps:
                change_framerate_ffmpeg(video_info["video_pathstring"], str(output_path), min_fps)
            else:
                copyfile(video_info["video_pathstring"], str(output_path))

        return None

