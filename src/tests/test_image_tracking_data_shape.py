from pathlib import Path
from typing import Union
import numpy as np
import pytest

from src.utilities.video import get_frame_count_of_videos, get_video_paths

@pytest.mark.usefixtures("synchronized_video_folder_path", "image_tracking_data_file_path")
def test_image_tracking_data_shape(synchronized_video_folder_path: Union[str, Path], image_tracking_data_file_path):
    assert Path(image_tracking_data_file_path).is_file(), f"{image_tracking_data_file_path} is not a file"
    
    image_tracking_data = np.load(image_tracking_data_file_path)
    list_of_video_paths = get_video_paths(Path(synchronized_video_folder_path))
    number_videos = len(list_of_video_paths)

    assert image_tracking_data.shape[0] == number_videos, f"Number of videos in {image_tracking_data_file_path} does not match number of videos in {synchronized_video_folder_path}"

    frame_count = get_frame_count_of_videos(synchronized_video_folder_path)

    assert len(set(frame_count)) == 1, f"Videos in {synchronized_video_folder_path} have different frame counts: {frame_count}"

    assert image_tracking_data.shape[1] == frame_count[0], f"Number of frames in {image_tracking_data_file_path} does not match number of frames of videos in {synchronized_video_folder_path}"

    assert image_tracking_data.shape[3] == 3, f"Data has {image_tracking_data.shape[3]} dimensions, expected 3 dimensions (XYZ)"
