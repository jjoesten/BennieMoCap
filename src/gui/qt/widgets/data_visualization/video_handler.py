import logging
logger = logging.getLogger(__name__)
from pathlib import Path
from typing import Union
import cv2
import numpy as np
from PyQt6 import QtGui
from PyQt6.QtCore import Qt

class VideoHandler():
    def __init__(self, video_path: Path):
        self._video_path = video_path
        self._cap = cv2.VideoCapture(str(video_path))
        self._frame_count = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))

    @property
    def frame_count(self) -> int:
        return self._frame_count

    def get_image_for_frame_number(self, frame_number: int) -> np.ndarray:
        self._set_video_to_frame(frame_number-1)
        image = self._read_frame_from_video()
        return image
    
    def _set_video_to_frame(self, frame_number: int):
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

    def _read_frame_from_video(self) -> Union[None, np.ndarray]:
        success, image = self._cap.read()
        if not success:
            logger.exception(f"Error reading image from {Path(self._video_path).name}")
            raise Exception
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image