import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from typing import Callable, Union
import numpy as np
from aniposelib.boards import CharucoBoard as AniposeCharucoBoard

from src.core_processes.capture_volume_calibration.anipose_camera_calibration import anipose_lib
from src.core_processes.capture_volume_calibration.charuco.charuco_board_definition import CharucoBoardDefinition
from src.utilities.video import get_video_paths
from src.system.paths_and_filenames.path_getters import (
    create_camera_calibration_file_name,
    get_calibrations_folder_path,
    get_last_successful_calibration_toml_path
)

class AniposeCameraCalibrator:
    def __init__(
        self,
        charuco_board_object: CharucoBoardDefinition,
        charuco_square_size: Union[int, float],
        calibration_videos_folder_path: Union[str, Path],
        progress_callback: Callable[[str], None] = None,
    ):
        self._charuco_board = charuco_board_object
        self._progress_callback = progress_callback
        self._charuco_square_size = charuco_square_size,

        if charuco_square_size == 1:
            logger.warning("Charuco square size is not set, so units of 3d reconstructed data will be in units of `however_long_the_black_edge_of_the_charuco_square_was`. Please input `charuco_square_size` in millimeters (or your preferred unity of length)")

        self._calibration_videos_folder_path = Path(calibration_videos_folder_path)
        self._session_folder_path = self._calibration_videos_folder_path.parent
        self._video_paths = get_video_paths(self._calibration_videos_folder_path)
        self._initialize_anipose_objects()

    def _initialize_anipose_objects(self):
        camera_names = [video_path.stem for video_path in self._video_paths]
        self._anipose_camera_group_object = anipose_lib.CameraGroup.from_names(camera_names)

        self._anipose_camera_group_object.metadata["charuco_square_size"] = self._charuco_square_size
        self._anipose_camera_group_object.metadata["charco_board_object"] = str(self._charuco_board)
        self._anipose_camera_group_object.metadata["path_to_recorded_videos"] = str(self._calibration_videos_folder_path)
        self._anipose_camera_group_object.metadata["date_time_calibrated"] = str(np.datetime64("now"))

        self._anipose_charuco_board = AniposeCharucoBoard(
            self._charuco_board.squares_width,
            self._charuco_board.squares_height,
            square_length=self._charuco_square_size,
            marker_length=self._charuco_square_size * 0.8,
            marker_bits=4,
            dict_size=250,
        )

    def calibrate_camera_capture_volume(self, pin_camera_0_to_origin: bool = False):
        list_of_list_of_video_paths = [[str(video_path) for video_path in self._video_paths]]

        (
            error,
            charuco_frame_data,
            charuco_frame_numbers,
        ) = self._anipose_camera_group_object.calibrate_videos(list_of_list_of_video_paths, self._anipose_charuco_board)
        success_str = "Anipose Calibration Successful"
        logger.info(success_str)
        self._progress_callback(success_str)

        if pin_camera_0_to_origin:
            # translate cameras so camera 0 is on (0,0,0)
            self._anipose_camera_group_object = self.pin_camera_0_to_origin(self._anipose_camera_group_object)

        calibration_toml_filename = create_camera_calibration_file_name(session_name=self._calibration_videos_folder_path.parent.stem)
        calibration_toml_path = Path(get_calibrations_folder_path()) / calibration_toml_filename
        self._anipose_camera_group_object.dump(calibration_toml_path)
        logger.info(f"anipose camera calibration data saved to Calibration folder: {str(calibration_toml_path)}")

        session_toml_path = Path(self._session_folder_path) / calibration_toml_filename
        self._anipose_camera_group_object.dump(session_toml_path)
        logger.info(f"anipose camera calibration data saved to Session folder: {str(session_toml_path)}")

        last_successful_calibration_toml_path = get_last_successful_calibration_toml_path()
        self._anipose_camera_group_object.dump(last_successful_calibration_toml_path)
        logger.info(f"anipose camera calibration data saved to 'Last Successful Calibration': {str(last_successful_calibration_toml_path)}")

    def pin_camera_0_to_origin(self, _anipose_cameera_group_object: anipose_lib.CameraGroup) -> anipose_lib.CameraGroup:
        original_translation_vectors = _anipose_cameera_group_object.get_translations()
        camera_0_translation = original_translation_vectors[0, :]
        altered_translation_vectors = np.zeros(original_translation_vectors.shape)

        for camera_number in range(original_translation_vectors.shape[0]):
            altered_translation_vectors[camera_number, :] = original_translation_vectors[camera_number, :] - camera_0_translation

        _anipose_cameera_group_object.set_translations(altered_translation_vectors)
        logger.info(f"original translation vectors:\n {original_translation_vectors}")
        logger.info(f"altered translation vectors:\n {_anipose_cameera_group_object.get_translations()}")
        return _anipose_cameera_group_object