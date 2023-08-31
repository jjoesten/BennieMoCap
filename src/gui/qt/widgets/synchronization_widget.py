import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from typing import Union

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QGridLayout
)

MAX_COLUMN_COUNT = 3

from src.gui.qt.widgets.data_visualization.single_video_display import SingleVideoDisplay
from src.utilities.video import get_video_paths

class SynchronizationWidget(QWidget):

    def __init__(self, video_folder_path: Union[str, Path] = None):
        super().__init__()

        self._layout = QGridLayout()
        self.setLayout(self._layout)

        if video_folder_path is not None:
            self.generate_video_display(video_folder_path)

    @property
    def video_players(self) -> list[SingleVideoDisplay]:
        return self._video_players


    def generate_video_display(self, video_folder_path: Union[str, Path]):
        video_paths = get_video_paths(video_folder_path)
        self._video_players = []

        c = 0
        r = 0
        for video_path in video_paths:
            video_player = SingleVideoDisplay(path_to_video=video_path)
            video_player.update_display()
            self._video_players.append(video_player)
            self._layout.addWidget(video_player, r, c)
            c += 1
            if c % MAX_COLUMN_COUNT == 0:
                c = 0
                r += 1


