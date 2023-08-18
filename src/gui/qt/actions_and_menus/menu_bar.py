from PyQt6.QtWidgets import QMainWindow, QMenuBar

from src.gui.qt.actions_and_menus.actions import Actions

class MenuBar(QMenuBar):
    def __init__(self, actions: Actions, parent: QMainWindow = None):
        super().__init__(parent=parent)

        file_menu = self.addMenu("&File")

        file_menu.addAction(actions.create_new_session_action)
        file_menu.addAction(actions.load_existing_session_action)
        file_menu.addSeparator()
        file_menu.addAction(actions.kill_threads_and_processes_action)
        file_menu.addAction(actions.reboot_gui_action)
        file_menu.addAction(actions.exit_action)

        help_menu = self.addMenu("&Help")