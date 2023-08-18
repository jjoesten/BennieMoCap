from pathlib import Path
import time
from datetime import datetime
from typing import Union

import logging
logger = logging.getLogger(__name__)

import toml

from src.system.paths_and_filenames.folder_and_filenames import (
    BASE_DATA_FOLDER_NAME,
    SESSIONS_FOLDER_NAME,
    LOGS_INFO_AND_SETTINGS_FOLDER_NAME,
    MOST_RECENT_SESSION_TOML_FILENAME,
    CALIBRATIONS_FOLDER_NAME,
    LOG_FILE_FOLDER_NAME,
    STYLESHEET_FOLDER_PATH_FROM_ROOT,
    QT_SCSS_FILENAME,
    QT_CSS_FILENAME,
)

data_folder_path: Path = None
session_folder_path: Path = None

def home_dir() -> Path:
    return Path.home()

def create_log_file_name() -> str:
    return "log_" + time.strftime("%m-%d-%Y-%H_%M_%S") + ".log"

def create_camera_calibration_file_name(session_name: str) -> str:
    return f"{session_name}_camera_calibration.toml"

def get_calibrations_folder_path(create_folder: bool = True) -> Path:
    calibration_folder_path = Path(get_data_folder_path()) / CALIBRATIONS_FOLDER_NAME
    if create_folder:
        calibration_folder_path.mkdir(exist_ok=True, parents=True)
    return calibration_folder_path

def get_log_file_path() -> Path:
    log_folder_path = Path(get_data_folder_path()) / LOGS_INFO_AND_SETTINGS_FOLDER_NAME / LOG_FILE_FOLDER_NAME
    log_folder_path.mkdir(exist_ok=True, parents=True)
    log_file_path = log_folder_path / create_log_file_name()
    return log_file_path

def get_data_folder_path(create_folder: bool = True) -> Path:
    global data_folder_path
    if data_folder_path is None:
        data_folder_path = Path(home_dir(), BASE_DATA_FOLDER_NAME)
        if create_folder:
            data_folder_path.mkdir(exist_ok=create_folder, parents=True)

    return data_folder_path

def _session_time_tag_format():
    return "%Y-%m-%d_%H_%M_%S"

def default_session_name(tag: str = None) -> str:
    if tag is not None:
        tag = f"_{tag}"
    else:
        tag = ""
    session_name = time.strftime(f"session_{_session_time_tag_format()}" + tag)
    logger.debug(f"Creating default session name: {session_name}")
    return session_name

def create_new_session_folder() -> Path:
    global session_folder_path
    if session_folder_path is None:
        session_folder_path = Path(get_sessions_folder_path()) / default_session_name()
    return session_folder_path

def get_sessions_folder_path(create_folder: bool = True) -> Path:
    session_folder_path = Path(get_data_folder_path()) / SESSIONS_FOLDER_NAME
    if create_folder:
        session_folder_path.mkdir(exist_ok=create_folder, parents=True)
    return session_folder_path

def get_most_recent_session_toml_path() -> Path:
    return Path(get_logs_info_and_settings_folder_path()) / MOST_RECENT_SESSION_TOML_FILENAME

def get_most_recent_session_path(subfolder:str = None):
    if not Path(get_most_recent_session_toml_path()).exists():
        logger.error(f"{MOST_RECENT_SESSION_TOML_FILENAME} not found at {get_most_recent_session_toml_path()}")
        return None
    session_dict = toml.load(str(get_most_recent_session_toml_path()))
    session_path = session_dict["most_recent_session_path"]
    if not Path(session_path).exists():
        logger.error(f"Most recent session path {session_path} not found!")
        return None
    if subfolder is not None:
        # check if subfolder is specified in the toml file, else return default
        try:
            subfolder_path = session_dict[subfolder]
        except KeyError:
            subfolder_path = Path(session_path) / subfolder
        return subfolder_path
    else:
        return session_path

def get_logs_info_and_settings_folder_path(create_folder: bool = True) -> Path:
    path = Path(get_data_folder_path()) / LOGS_INFO_AND_SETTINGS_FOLDER_NAME
    if create_folder:
        path.mkdir(exist_ok=create_folder, parents=True)
    return path

def get_scss_stylesheet_path() -> Path:
    return Path(__file__).parent.parent.parent / STYLESHEET_FOLDER_PATH_FROM_ROOT / QT_SCSS_FILENAME

def get_css_stylesheet_path() -> Path:
    return Path(__file__).parent.parent.parent / STYLESHEET_FOLDER_PATH_FROM_ROOT / QT_CSS_FILENAME
