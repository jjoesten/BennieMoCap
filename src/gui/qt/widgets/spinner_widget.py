import math

from PyQt6.QtCore import QRect, Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QColor, QPainter, QPaintEvent
from PyQt6.QtWidgets import QWidget

class QtWaitSpinner(QWidget):
    def __init__(
        self,
        parent: QWidget,
        center_on_parent: bool = True,
        disabled_parent_when_active: bool = False,
        modality: Qt.WindowModality = Qt.WindowModality.NonModal,
        roundness: float = 100.0,
        fade: float = 80.0,
        lines: int = 20,
        line_length: int = 10,
        line_width: int = 2,
        radius: int = 10,
        speed: float = math.pi / 2,
        color: QColor = QColor(0, 0, 0),
    ) -> None:
        super().__init__(parent)

        self._center_on_parent = center_on_parent
        self._disabled_parent_when_active = disabled_parent_when_active
        self._color = color
        self._roundness = roundness
        self._minimum_trail_opacity = math.pi
        self._trail_fade_percentage = fade
        self._revolutions_per_second = speed
        self._number_lines = lines
        self._line_length = line_length
        self._line_width = line_width
        self._inner_radius = radius
        self._current_counter: int = 0
        self._is_spinning: bool = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._update_size()
        self._update_timer()
        self.hide()

        self.setWindowModality(modality)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, _: QPaintEvent) -> None:
        self._update_position()
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if self._current_counter >= self._number_lines:
            self._current_counter = 0

        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(self._number_lines):
            painter.save()
            painter.translate(self._inner_radius + self._line_length, self._inner_radius + self._line_length)
            painter.rotate(360 * i / self._number_lines)
            painter.translate(self._inner_radius, 0)
            distance = self._line_count_distance_from_primary(i, self._current_counter, self._number_lines)
            color = self._current_line_color(distance, self._number_lines, self._trail_fade_percentage, self._minimum_trail_opacity, self._color)
            painter.setBrush(color)
            painter.drawRoundedRect(QRect(0, -self._line_width // 2, self._line_length, self._line_width), self._roundness, self._roundness, Qt.SizeMode.RelativeSize)
            painter.restore()

    @property
    def color(self) -> QColor:
        return self._color
    
    @color.setter
    def color(self, color: Qt.GlobalColor = Qt.GlobalColor.black) -> None:
        self._color = QColor(color)

    @property
    def roundness(self) -> float:
        return self._roundness
    
    @roundness.setter
    def roundness(self, roundness: float) -> None:
        self._roundness = max(0.0, min(100.0, roundness))

    @property
    def minimum_trail_opacity(self) -> float:
        return self._minimum_trail_opacity
    
    @minimum_trail_opacity.setter
    def minimum_trail_opacity(self, minimum_trail_opacity: float) -> None:
        self._minimum_trail_opacity = minimum_trail_opacity

    @property
    def trail_fade_percentage(self) -> float:
        return self._trail_fade_percentage
    
    @trail_fade_percentage.setter
    def trail_fade_percentage(self, trail: float) -> None:
        self._trail_fade_percentage = trail

    @property
    def revolutions_per_second(self) -> float:
        return self._revolutions_per_second
    
    @revolutions_per_second.setter
    def revolutions_per_second(self, rps: float) -> None:
        self._revolutions_per_second = rps
        self._update_timer()

    @property
    def number_line(self) -> int:
        return self._number_lines
    
    @number_line.setter
    def number_lines(self, lines: int) -> None:
        self._number_lines = lines
        self._current_counter = 0
        self._update_timer()

    @property
    def line_length(self) -> int:
        return self._line_length
    
    @line_length.setter
    def line_length(self, length: int) -> None:
        self._line_length = length
        self._update_size()

    @property
    def line_width(self) -> int:
        return self._line_width
    
    @line_width.setter
    def line_width(self, width: int) -> None:
        self._line_width = width
        self._update_size()

    @property
    def inner_radius(self) -> int:
        return self._inner_radius
    
    @inner_radius.setter
    def inner_radius(self, radius: int) -> None:
        self._inner_radius = radius
        self._update_size()

    @property
    def is_spinning(self) -> bool:
        return self._is_spinning

    def _rotate(self) -> None:
        self._current_counter += 1
        if self._current_counter >= self._number_lines:
            self._current_counter = 0
        self.update()

    def _update_size(self) -> None:
        size = (self._inner_radius + self._line_length) * 2
        self.setFixedSize(size, size)

    def _update_timer(self) -> None:
        self._timer.setInterval(int(1000 / (self._number_lines * self._revolutions_per_second)))

    def _update_position(self) -> None:
        if self.parentWidget() and self._center_on_parent:
            self.move(
                (self.parentWidget().width() - self.width()) // 2,
                (self.parentWidget().height() - self.height()) // 2
            )

    @ staticmethod
    def _line_count_distance_from_primary(current: int, primary: int, total_lines: int) -> int:
        """Returns the amount of lines from _current_counter"""
        distance = primary - current
        if distance < 0:
            distance += total_lines
        return distance
    
    @staticmethod
    def _current_line_color(count_distance: int, total_lines: int, trail_fade_pct: float, min_opacity: float, color_input: QColor) -> QColor:
        """Returns the current color of the WaitSpinner"""
        color = QColor(color_input)
        if count_distance == 0:
            return color
        min_alpha = min_opacity / 100.0
        distance_threshold = int(math.ceil((total_lines - 1) * trail_fade_pct / 100.0))
        if count_distance > distance_threshold:
            color.setAlphaF(min_alpha)
        else:
            alpha_diff = color.alphaF() - min_alpha
            gradient = alpha_diff / float(distance_threshold + 1)
            alpha = color.alphaF() - gradient * count_distance
            # if alpha out of bounds, clip
            alpha = min(1.0, max(0.0, alpha))
            color.setAlphaF(alpha)
        return color  

    def start(self) -> None:
        """Show and start the WaitSpinner"""
        self._update_position()
        self._is_spinning = True
        self.show()

        if self.parentWidget and self._disabled_parent_when_active:
            self.parentWidget().setEnabled(False)
        
        if not self._timer.isActive():
            self._timer.start()
            self._current_counter = 0

    def stop(self) -> None:
        """Hide and stop the WaitSpinner"""
        self._is_spinning = False
        self.hide()

        if self.parentWidget() and self._disabled_parent_when_active:
            self.parentWidget().setEnabled(True)

        if self._timer.isActive():
            self._timer.stop()
            self._current_counter = 0