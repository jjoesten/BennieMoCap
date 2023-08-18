from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget
)

class ControlPanelWidget(QWidget):
    def __init__(
        self,
        # TODO: pass in widgets for control panel
        parent=None
    ):
        super().__init__(parent=parent)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._tab_widget = QTabWidget()
        self._layout.addWidget(self._tab_widget)

        # TODO: Add Tabs

        self._tab_widget.setProperty("control_panel_tabs", True)
        self.style().polish(self._tab_widget)

    @property
    def tab_widget(self) -> QTabWidget:
        return self._tab_widget