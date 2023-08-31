import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from typing import Union
from collections import deque
import numpy as np

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QFrame,
    QGroupBox
)

from src.gui.qt.widgets.data_visualization.video_handler import VideoHandler
from src.gui.qt.widgets.data_visualization.slider_widget import VideoSlider

MAX_BUFFER_LENGTH = 5

class SingleVideoDisplay(QFrame):
    video_loaded_signal = pyqtSignal()

    def __init__(self, path_to_video: Union[str, Path], show_buttons: bool = False):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._video_name = Path(path_to_video).stem

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        label = QLabel(Path(path_to_video).name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(label)

        self._video_layout = QVBoxLayout()
        self._video_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addLayout(self._video_layout)

        self._slider = VideoSlider(show_buttons=show_buttons)
        self._slider.setEnabled(False)
        self._slider.slider.valueChanged.connect(self._handle_slider_value_changed)
        self._layout.addWidget(self._slider)

        if path_to_video is not None:
            self.generate_video_display(path_to_video)

        self._layout.addStretch()

    @property
    def current_frame(self):
        return self._slider.current_frame
    
    @property
    def video_name(self):
        return self._video_name


    def generate_video_display(self, path_to_video: Union[str, Path]):
        self._video_handler = VideoHandler(path_to_video)
         
        self._image_widget = QLabel()
        self._image_widget.setMinimumSize(200, 200)
        self._video_layout.addWidget(self._image_widget)

        self._slider.set_slider_range(self._video_handler.frame_count)
        self._slider.setEnabled(True)
        
        self.video_loaded_signal.emit()

    def update_display(self, frame_number: int = None):
        if frame_number is None:
            frame_number = self._slider.slider.value()

        try:
            image = self._video_handler.get_image_for_frame_number(frame_number)
            self._set_pixmap_from_image(image)
        except Exception as e:
            logger.warning(f"Error updating display for video {self._video_handler._video_path.name}: e")

    def _set_pixmap_from_image(self, image: np.ndarray):
        qimage = QImage(image.data, image.shape[1], image.shape[0], QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)

        image_label_width = self._image_widget.width()
        image_label_height = self._image_widget.height()
        scaled_width = int(image_label_width)
        scaled_height = int(image_label_height)

        pixmap = pixmap.scaled(scaled_width, scaled_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self._image_widget.setPixmap(pixmap)

    def _handle_slider_value_changed(self):
        self.update_display(self._slider.current_frame)