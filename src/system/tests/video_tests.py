from pathlib import Path
from typing import Union

import pytest

from src.utilities.video import get_video_paths, get_frame_count_of_videos, get_framerates_of_videos

@pytest.mark.usefixtures("synchronized_videos_folder")
def test_video_framerates(synchronized_videos_folder: Union[str, Path]):
    video_paths = get_video_paths(synchronized_videos_folder)
    assert len(video_paths) > 0, f"No videos found in {synchronized_videos_folder}"
    framerates = get_framerates_of_videos(synchronized_videos_folder)
    assert len(set(framerates)) == 1, f"Videos in {synchronized_videos_folder} have different framerates: {framerates}"

@pytest.mark.usefixtures("synchronized_videos_folder")
def test_video_frame_counts(synchronized_videos_folder: Union[str, Path]):
    video_paths = get_video_paths(synchronized_videos_folder)
    assert len(video_paths) > 0, f"No videos found in {synchronized_videos_folder}"
    frame_counts = get_frame_count_of_videos(synchronized_videos_folder)
    assert len(set(frame_counts)) == 1, f"Videos in {synchronized_videos_folder} have different frame counts: {frame_counts}"