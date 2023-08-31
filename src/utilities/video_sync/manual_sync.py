import logging
logger = logging.getLogger(__name__)

import time
import toml

from pathlib import Path
from typing import List

from src.utilities.video import get_video_paths, create_video_info_dict, get_fps_list, trim_videos, get_frame_count_of_videos
from src.utilities.list import check_list_values_are_equal
from src.utilities.dict import save_dictionaries_to_toml

RAW_VIDEO_NAME = "Raw_video_information"
SYNCHRONIZED_VIDEO_NAME = "Synchronized_video_information"
LAG_DICTIONARY_NAME = "Lag_dictionary"
DEBUG_TOML_NAME = "synchronization_debug.toml"

def synchronize_videos_manually(
    raw_video_folder_path: Path,
    synchronized_video_folder_path: Path,
    keypoint_dict: dict,
    video_handler: str = "deffcode",
):
    start_timer = time.time()

    video_paths_list = get_video_paths(video_folder=raw_video_folder_path)
    # TODO: this makes no sense (the if test)
    if synchronized_video_folder_path is None or not synchronized_video_folder_path.exists():
        Path(synchronized_video_folder_path).mkdir(exist_ok=True, parents=True)
    synchronized_video_folder_path = Path(synchronized_video_folder_path)

    video_info_dict = create_video_info_dict(video_filepath_list=video_paths_list)    
    
    fps_list = get_fps_list(video_info_dict=video_info_dict)
    fps = check_list_values_are_equal(input_list=fps_list)

    # FIND LAGS
    comparison_file_key = next(iter(keypoint_dict))
    lag_dict = {
        camera_name: ((keypoint_dict[comparison_file_key] - keypoint)/fps) for camera_name, keypoint in keypoint_dict.items()
    }
    normalized_lag_dict = {
        camera_name: (max(lag_dict.values()) - value) for camera_name, value in lag_dict.items()
    }

    logger.info(f"original lag dict: {lag_dict} normalized_lag_dict: {normalized_lag_dict}")

    trim_videos(
        video_info_dict=video_info_dict,
        synchronized_folder_path=synchronized_video_folder_path,
        lag_dict=normalized_lag_dict,
        fps=fps,
        video_handler=video_handler
    )

    synchronized_video_framecounts = get_frame_count_of_videos(folder_path=synchronized_video_folder_path)
    logger.info(f"All videos are {check_list_values_are_equal(synchronized_video_framecounts)} frames long")

    syncronized_videos_info_dict = create_video_info_dict(video_filepath_list=get_video_paths(synchronized_video_folder_path))

    save_dictionaries_to_toml(
        input_dictionaries={
            RAW_VIDEO_NAME: video_info_dict,
            SYNCHRONIZED_VIDEO_NAME: syncronized_videos_info_dict,
            LAG_DICTIONARY_NAME: lag_dict,
        },
        output_file_path=synchronized_video_folder_path / DEBUG_TOML_NAME
    )

    end_timer = time.time()
    logger.info(f"Elapsed processing time in seconds: {end_timer - start_timer}")

    return synchronized_video_folder_path