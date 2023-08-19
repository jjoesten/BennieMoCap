import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from typing import Dict, Union
import subprocess
from shutil import copyfile
import cv2
import debugpy

def get_video_paths(video_folder: Union[str, Path]) -> list:
    list_of_video_paths = list(Path(video_folder).glob("*.mp4")) + list(Path(video_folder).glob("*.MP4"))
    unique_list_of_video_paths = _get_unique_list(list_of_video_paths)
    return unique_list_of_video_paths

def _get_unique_list(list: list) -> list:
    unique_list = []
    [unique_list.append(element) for element in list if element not in unique_list]
    return unique_list

def _extract_video_duration_ffmpeg(file_pathstring: str):
    debugpy.debug_this_thread()
    extract_duration_subprocess = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_pathstring,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    video_duration = float(extract_duration_subprocess.stdout)
    return video_duration

def _extract_video_fps_ffmpeg(file_pathstring: str) -> float:
    debugpy.debug_this_thread()
    extract_fps_subprocess = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=r_frame_rate",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_pathstring,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    cleaned = str(extract_fps_subprocess.stdout).split("'")[1].split("\\")[0]
    numerator, denominator = cleaned.split("/")
    video_fps = float(int(numerator)/int(denominator))
    return video_fps

def extract_video_audio_sample_rate(file_pathstring: str):
    debugpy.debug_this_thread()
    extract_sample_rate_subprocess = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            "-show_entries",
            "stream=sample_rate",
            file_pathstring,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    try:
        sample_rate = float(extract_sample_rate_subprocess.stdout)
        return sample_rate
    except Exception as e:
        logger.error("Unable to determine audio sample rate. Video file may not have audio track.")
        logger.exception(e)
        raise Exception(e)

def create_video_info_dict(
        video_filepath_list: list
) -> Dict[str, dict]:
    debugpy.debug_this_thread()
    video_info_dict = dict()
    for video_filepath in video_filepath_list:
        video_dict = dict()
        video_dict["video_filepath"] = video_filepath
        video_dict["video_pathstring"] = str(video_filepath)
        video_name = video_filepath.stem
        video_dict["camera_name"] = video_name

        video_dict["video_duration"] = _extract_video_duration_ffmpeg(file_pathstring=str(video_filepath))
        video_dict["video_fps"] = _extract_video_fps_ffmpeg(file_pathstring=str(video_filepath))

        video_info_dict[video_name] = video_dict

    return video_info_dict

def get_fps_list(video_info_dict: Dict[str, dict]):
    return [video_dict["video_fps"] for video_dict in video_info_dict.values()]



def change_framerate_ffmpeg(input_video_pathstring: str, output_video_pathstring: str, new_framerate: float):
    debugpy.debug_this_thread()
    change_framerate_subprocess = subprocess.run(
        [
            "ffmpeg",
            "-i",
            input_video_pathstring,
            "-filter:v",
            f"fps={new_framerate}",
            output_video_pathstring
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

def get_framerates_of_videos(folder_path: Union[str, Path]) -> list[float]:
    video_paths = get_video_paths(Path(folder_path))
    if len(video_paths) == 0:
        logger.error(f"No videos found in {folder_path}")
        return None
    framerate_list = []
    for video_path in video_paths:
        cap = cv2.VideoCapture(str(video_path))
        framerate_list.append(float(cap.get(cv2.CAP_PROP_FPS)))
        cap.release()
    return framerate_list

def get_frame_count_of_videos(folder_path: Union[str, Path]):
    video_paths = get_video_paths(Path(folder_path))
    if len(video_paths) == 0:
        logger.error(f"No videos found in {folder_path}")
        return None
    frame_count_list = []
    for video_path in video_paths:
        cap = cv2.VideoCapture(str(video_path))
        frame_count_list.append(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        cap.release()
    return frame_count_list
