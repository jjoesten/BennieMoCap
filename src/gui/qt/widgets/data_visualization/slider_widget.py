from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtWidgets import (
    QSlider,
    QWidget,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout
)

DEFAULT_FPS = 120

class QSliderButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setFixedWidth(75)

class VideoSlider(QWidget):
    def __init__(self, show_buttons: bool = True):
        super().__init__()

        self._timer = QTimer()
        self._timer.timeout.connect(self._timer_timeout)

        self._layout = QVBoxLayout(self)

        slider_hbox = QHBoxLayout()
        self._layout.addLayout(slider_hbox)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        slider_hbox.addWidget(self._slider)
        self._slider_max = 0
        self._slider.valueChanged.connect(lambda: self._frame_count_label.setText(f"Frame# {self._slider.value()}"))

        self._frame_count_label = QLabel(f"Frame# {self._slider.value()}")
        slider_hbox.addWidget(self._frame_count_label)

        button_layout = QHBoxLayout()
        self._layout.addLayout(button_layout)

        self._play_button = QSliderButton("Play")
        self._play_button.clicked.connect(self._play_button_clicked)
        button_layout.addWidget(self._play_button)

        self._pause_button = QSliderButton("Pause")
        self._pause_button.clicked.connect(self._pause_button_clicked)
        button_layout.addWidget(self._pause_button)

        self._stop_button = QSliderButton("Stop")
        self._stop_button.clicked.connect(self._reset_button_clicked)
        button_layout.addWidget(self._stop_button)

        if show_buttons == False:
            self._play_button.hide()
            self._pause_button.hide()
            self._stop_button.hide()
            

        self.set_frames_per_second(DEFAULT_FPS)

    @property
    def frames_per_second(self):
        return self._fps
    
    @property
    def frame_duration(self):
        return self._frame_duration
    
    @property
    def slider(self):
        return self._slider
    
    @property
    def current_frame(self):
        return self._slider.value()
    
    def set_frames_per_second(self, frames_per_second):
        self._frames_per_second = frames_per_second
        self._frame_duration = 1.0 / frames_per_second

    def set_slider_range(self, num_frames):
        self._slider_max = num_frames - 1
        self._slider.setValue(0)
        self._slider.setMaximum(self._slider_max)

    @pyqtSlot()
    def _timer_timeout(self):
        if self._slider.value() < self._slider_max:
            self._slider.setValue(self._slider.value() + 1)
        else:
            self._slider.setValue(0)

    @pyqtSlot()
    def _play_button_clicked(self):
        self._timer.stop()
        self._timer.start(0)

    @pyqtSlot()
    def _pause_button_clicked(self):
        self._timer.stop()

    @pyqtSlot()
    def _reset_button_clicked(self):
        self._timer.stop()
        self._timer.setValue()