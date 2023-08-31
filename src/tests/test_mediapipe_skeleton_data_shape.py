from pathlib import Path
from typing import Union
import numpy as np
import pytest

from src.utilities.video import get_frame_count_of_videos

@pytest.mark.usefixtures("synchronized_data_folder_path", "raw_skeleton_npy_file_path", "reprojection_error_file_path")
def test_mediapipe_skeleton_data_shape(
    synchronized_video_folder_path: Union[str, Path],
    raw_skeleton_npy_file_path: Union[str, Path],
    reprojection_error_file_path: Union[str, Path]
):
    
    assert Path(raw_skeleton_npy_file_path).is_file(), f"3d skeleton data file does not exist at {raw_skeleton_npy_file_path}"

    skel3d_framer_marker_xyz = np.load(raw_skeleton_npy_file_path)
    assert len(skel3d_framer_marker_xyz.shape) == 3, f"3d skeleton data file should have 3 dimensions - {raw_skeleton_npy_file_path}"
    # TODO: is this a duplicate test from above?
    assert skel3d_framer_marker_xyz.shape[2] == 3, f"3d skeleton data file does not have 3 dimensions for X,Y,Z - {raw_skeleton_npy_file_path}"

    assert Path(reprojection_error_file_path).is_file(), f"3d skeleton reprojection error data file does not exist at {reprojection_error_file_path}"

    reprojection_error = np.load(reprojection_error_file_path)
    assert len(reprojection_error.shape) == 2, f"3d skeleton reprojection error data file should have 2 dimensions {reprojection_error_file_path}"

    video_frame_counts = get_frame_count_of_videos(synchronized_video_folder_path)
    assert len(set(video_frame_counts)) == 1, f"Videos in {synchronized_video_folder_path} have different frame counts: {video_frame_counts}"

    frame_count = video_frame_counts[0]
    assert skel3d_framer_marker_xyz.shape[0] == frame_count
    assert reprojection_error.shape[0] == frame_count

    