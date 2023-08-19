from pathlib import Path

import src

# FOLDER / DIRECTORY NAMES
BASE_DATA_FOLDER_NAME = "benniemocap_data"
SESSIONS_FOLDER_NAME = "sessions"
CALIBRATIONS_FOLDER_NAME = "calibrations"
SYNCHRONIZED_VIDEOS_FOLDER_NAME = "synchronized_videos"
ANNOTATED_VIDEOS_FOLDER_NAME = "annotated_videos"
OUTPUT_DATA_FOLDER_NAME = "output_data"
RAW_DATA_FOLDER_NAME = "raw_data"
LOGS_INFO_AND_SETTINGS_FOLDER_NAME = "logs_info_and_settings"
LOG_FILE_FOLDER_NAME = "logs"

STYLESHEET_FOLDER_PATH_FROM_ROOT = "gui/qt/stylesheets"

# FILENAMES
QT_SCSS_FILENAME = "qt_stylesheet.scss"
QT_CSS_FILENAME = "qt_stylesheet.css"
MOST_RECENT_SESSION_TOML_FILENAME = "most_recent_session.toml"


# logo
PATH_TO_LOGO_SVG = Path(src.__file__).parent / "assets/logo/BennieLogo.svg"
PATH_TO_LOGO_PNG = Path(src.__file__).parent / "assets/logo/BennieLogoBlackFill.png"