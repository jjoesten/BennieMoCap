import logging
logger = logging.getLogger(__name__)
from collections import deque
from pathlib import Path
from typing import Union
import numpy as np

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
)

from src.gui.qt.widgets.data_visualization.video_handler import VideoHandler

MAX_COLUMN_COUNT = 2
MAX_BUFFER_LENGTH = 5

class MultiVideoDisplay(QWidget):
    videos_loaded_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._video_display_layout = QGridLayout()
        self._layout.addLayout(self._video_display_layout)

        self._update_worker = UpdateDisplayWorker([])

    @property
    def frame_count(self) -> int:
        return int(self._video_handler_dictionary[0].frame_count)

    def generate_video_display(self, path_to_videos: Union[str, Path]):
        self._video_handler_dictionary = self._create_video_handlers(list(Path(path_to_videos).glob('*.mp4')))
        self._image_label_widget_dictionary = self._create_image_label_widgets_for_videos(number_videos=len(self._video_handler_dictionary))
        self._add_widgets_to_layout()
        
        self._update_worker.video_handlers = list(self._video_handler_dictionary.values())
        self._update_worker.updated.connect(self.update_display)

        self.videos_loaded_signal.emit()

    def update_display(self, frame_number: int):
        try:
            for video_handler, image_label_widget in zip(self._video_handler_dictionary.values(), self._image_label_widget_dictionary.values()):
                image = video_handler.get_image_for_frame_number(frame_number)
                self._set_pixmap_from_image(image_label_widget, image)
        except Exception as e:
            logger.warning(f"Error updating display for video {video_handler.video_path.name}: e")

    def start_update_worker(self):
        self._update_worker.start()

    def stop_update_worker(self):
        self._update_worker.terminate()

    def _create_video_handlers(self, video_paths: list) -> dict:
        self._video_handler_dictionary = {}
        for count, video_path in enumerate(video_paths):
            self._video_handler_dictionary[count] = VideoHandler(video_path)
        return self._video_handler_dictionary
    
    def _create_image_label_widgets_for_videos(self, number_videos: int):
        label_widget_dictionary = {}
        for video_number in range(number_videos):
            label_widget_dictionary[video_number] = QLabel(f"Video {video_number}")
            label_widget_dictionary[video_number].setMinimumSize(200, 200)
        return label_widget_dictionary

    def _add_widgets_to_layout(self):
        column_count = 0
        row_count = 0
        for widget in self._image_label_widget_dictionary:
            self._video_display_layout.addWidget(self._image_label_widget_dictionary[widget], row_count, column_count)

            # grid formatting
            column_count += 1
            if column_count % MAX_COLUMN_COUNT == 0:
                column_count = 0
                row_count += 1

    def _set_pixmap_from_image(self, image_label_widget: QLabel, image: np.ndarray):
        q_image = self._convert_image_to_qimage(image)
        pixmap = QPixmap.fromImage(q_image)

        scaled_width = int(image_label_widget.width())
        scaled_height = int(image_label_widget.height())

        pixmap = pixmap.scaled(scaled_width, scaled_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        image_label_widget.setPixmap(pixmap)

    def _convert_image_to_qimage(self, image: np.ndarray) -> QImage:
        return QImage(image.data, image.shape[1], image.shape[0], QImage.Format.Format_RGB888)
    

class UpdateDisplayWorker(QThread):
    updated = pyqtSignal(np.ndarray, int)

    def __init__(self, video_handlers):
        super().__init__()
        self.video_handlers = video_handlers
        self.buffer = deque(maxlen=MAX_BUFFER_LENGTH)

    def run(self):
        while True:
            for i, vh in enumerate(self.video_handlers):
                frame = vh.get_iamge_for_frame_number(vh.current_frame_number)
                self.buffer.append((frame, i))

                if len(self.buffer) == MAX_BUFFER_LENGTH:
                    for frame, video_number in self.buffer:
                        self.updated.emit(frame, video_number)

                    self.buffer.clear()