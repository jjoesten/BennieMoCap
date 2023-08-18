from PyQt6.QtGui import QAction

CREATE_NEW_SESSION_ACTION_NAME = "Create &New Session"
LOAD_EXISTING_SESSION_ACTION_NAME = "&Load Existing Session"
REBOOT_GUI_ACTION_NAME = "&Reboot"
KILL_THREADS_AND_PROCESSES_ACTION_NAME = "&Kill Threads and Processes"
EXIT_ACTION_NAME = "E&xit"

class Actions:
    def __init__(self, main_window):
        self.create_new_session_action = QAction(CREATE_NEW_SESSION_ACTION_NAME, parent=main_window)
        self.create_new_session_action.setShortcut("Ctrl+N")
        self.create_new_session_action.triggered.connect(main_window.handle_start_new_session_action)

        self.load_existing_session_action = QAction(LOAD_EXISTING_SESSION_ACTION_NAME, parent=main_window)
        self.load_existing_session_action.setShortcut("Ctrl+L")
        self.load_existing_session_action.triggered.connect(main_window.handle_load_existing_session_action)

        self.reboot_gui_action = QAction(REBOOT_GUI_ACTION_NAME, parent=main_window)
        self.reboot_gui_action.setShortcut("Ctrl+R")
        self.reboot_gui_action.triggered.connect(main_window.reboot_gui)

        self.kill_threads_and_processes_action = QAction(KILL_THREADS_AND_PROCESSES_ACTION_NAME, parent=main_window)
        self.kill_threads_and_processes_action.setShortcut("Ctrl+Z")
        self.kill_threads_and_processes_action.triggered.connect(main_window.kill_threads_and_processes)

        self.exit_action = QAction(EXIT_ACTION_NAME, parent=main_window)
        self.exit_action.setShortcut("Ctrl+X")
        self.exit_action.triggered.connect(main_window.close)