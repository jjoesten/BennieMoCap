from pathlib import Path

import src

# FOLDER / DIRECTORY NAMES
BASE_DATA_FOLDER_NAME = "benniemocap_data"
SESSIONS_FOLDER_NAME = "sessions"
CALIBRATIONS_FOLDER_NAME = "calibrations"
SYNCHRONIZED_VIDEOS_FOLDER_NAME = "synchronized_videos"
FRAMERATE_MATCHED_VIDEOS_FOLDER_NAME = "framerate_matched_videos"
AUDIO_FOLDER_NAME = "audio_files"
ANNOTATED_VIDEOS_FOLDER_NAME = "annotated_videos"
OUTPUT_DATA_FOLDER_NAME = "output_data"
RAW_DATA_FOLDER_NAME = "raw_data"
LOGS_INFO_AND_SETTINGS_FOLDER_NAME = "logs_info_and_settings"
LOG_FILE_FOLDER_NAME = "logs"
CENTER_OF_MASS_FOLDER_NAME = "center_of_mass"

STYLESHEET_FOLDER_PATH_FROM_ROOT = "gui/qt/stylesheets"

# FILENAMES
QT_SCSS_FILENAME = "qt_stylesheet.scss"
QT_CSS_FILENAME = "qt_stylesheet.css"
MOST_RECENT_SESSION_TOML_FILENAME = "most_recent_session.toml"
SESSION_PARAMETERS_JSON_FILENAME = "session_parameters.json"
LAST_SUCCESSFUL_CALIBRATION_FILENAME = "last_successful_calibration.toml"
GUI_STATE_JSON_FILENAME = "gui_state.json"

MEDIAPIPE_2D_NPY_FILENAME = "mediapipe2dData_numCams_numFrames_numTrackedPoints_pixelXYZ.npy"
MEDIAPIPE_BODY_WORLD_FILENAME = "mediapipeBodyWorld_numCams_numFrames_numTrackedPoitnt_XYZ.npy"
RAW_MEDIAPIPE_3D_NPY_FILENAME = "mediapipe3dData_numFrames_numTrackedPoints_spatialXYZ.npy"
MEDIAPIPE_3D_NPY_FILENAME = "mediapipeSkel_3d_body_hands_face.npy"
MEDIAPIPE_REPROJECTION_ERROR_NPY_FILENAME = "mediapipe3dData_numFrames_numTrackedPoints_reprojectionError.npy"

MEDIAPIPE_BODY_3D_DATAFRAME_CSV_FILENAME = "mediapipe_body_3d_xyz.csv"
MEDIAPIPE_RIGHT_HAND_3D_DATAFRAME_CSV_FILENAME = "mediapipe_right_hand_3d_xyz.csv"
MEDIAPIPE_LEFT_HAND_3D_DATAFRAME_CSV_FILENAME = "mediapipe_left_hand_3d_xyz.csv"
MEDIAPIPE_FACE_3D_DATAFRAME_CSV_FILENAME = "mediapipe_face_3d_xyz.csv"

TOTAL_BODY_CENTER_OF_MASS_NPY_FILENAME = "total_body_com_xyz.npy"
SEGMENT_CENTER_OF_MASS_NPY_FILENAME = "segment_com_frame_joint_xyz.npy"

MEDIAPIPE_SKELETON_SEGMENT_LENGTHS_JSON_FILENAME = "mediapipe_skeleton_segment_lengths.json"
MEDIAPIPE_NAMES_AND_CONNECTIONS_JSON_FILENAME = "mediapipe_names_and_connections_dict.json"


# logo
PATH_TO_LOGO_SVG = Path(src.__file__).parent / "assets/logo/BennieLogo.svg"
PATH_TO_LOGO_PNG = Path(src.__file__).parent / "assets/logo/BennieLogoBlackFill.png"