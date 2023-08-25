import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from typing import Union
import cv2
import datetime
import os
import librosa
from skelly_synchronize.core_processes.audio_utilities import extract_audio_from_video_ffmpeg
from src.system.paths_and_filenames.path_getters import get_most_recent_session_path, get_synchronzied_videos_folder_path
from src.system.paths_and_filenames.folder_and_filenames import SYNCHRONIZED_VIDEOS_FOLDER_NAME
from src.utilities.video import extract_video_audio_sample_rate

class VideoModel:
    def __init__(self, video_path: Union[str, Path]):
        self._video_path = Path(video_path)
        self._filename = self._video_path.name

        cap = cv2.VideoCapture(str(self._video_path))
        
        self._fps = cap.get(cv2.CAP_PROP_FPS) 

        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        seconds = frame_count / self._fps
        self._duration = datetime.timedelta(seconds=seconds)

        self._resolution = str(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) + "x" + str(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self._size = str(os.path.getsize(self._video_path)/(1024*1024))

        try:
            self._audio_sample_rate = extract_video_audio_sample_rate(str(self._video_path))
        except Exception as e:
            self._audio_sample_rate = 0.0
            logger.error(f"Error gathering audio data for {self._video_path}")
            logger.exception(e)

        # extract_audio_from_video_ffmpeg(
        #     file_pathstring=str(self._video_path),
        #     file_name=self._filename,
        #     output_folder_path=str(get_synchronzied_videos_folder_path(get_most_recent_session_path())),
        #     output_extension="wav"
        # )

        # audio_name = self._filename + ".wav"
        # audio_file_path = get_synchronzied_videos_folder_path(get_most_recent_session_path()) / audio_name
        # _, sample_rate = librosa.load(path=audio_file_path, sr=None)
        # self._audio_sample_rate = sample_rate

        cap.release()

    @property
    def path(self) -> str:
        return Path(self._video_path)

    @property
    def filename(self) -> str:
        return self._filename
    
    @property
    def fps(self) -> float:
        return self._fps
    
    @property
    def duration(self) -> str:
        return self._duration
    
    @property
    def resolution(self) -> str:
        return self._resolution
    
    @property
    def size(self) -> str:
        return self._size
    
    @property
    def audio_sample_rate(self) -> float:
        return self._audio_sample_rate