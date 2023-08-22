import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from typing import Dict, Union
import subprocess
from shutil import copyfile
import cv2
import debugpy
import json
import cv2
from deffcode import FFdecoder, Sourcer

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
    
def trim_single_video_ffmpeg(
    input_video_pathstring: str,
    start_time: float,
    desired_duration: float,
    output_video_pathstring: str,
):
    subprocess.run(
        [
            "ffmpeg",
            "-i",
            f"{input_video_pathstring}",
            "-ss",
            f"{start_time}",
            "-t",
            f"{desired_duration}",
            "-y",
            f"{output_video_pathstring}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

def _check_if_video_has_reversed_metadata(video_pathstring: str):
    cap = cv2.VideoCapture(video_pathstring)
    if not cap.isOpened():
        raise Exception("Video could not be opened")
    cv2_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cv2_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    sourcer = Sourcer(video_pathstring).probe_stream()
    metadata_dict = sourcer.retrieve_metadata()
    deffcode_width = metadata_dict["source_video_resolution"][0]
    deffcode_height = metadata_dict["source_video_resolution"][1]

    if (cv2_width != deffcode_width) & (cv2_height != deffcode_height):
        return True
    else:
        return False

def trim_single_video_deffcode(
    input_video_pathstring: str,
    frame_list: list,
    output_video_pathstring: str,
):
    vertical_video_bool = _check_if_video_has_reversed_metadata(video_pathstring=input_video_pathstring)
    if vertical_video_bool:
        logging.info("Video has reveresed metadata, changing ffmpeg transpose argument")
        ffparams = {"-ffprefixes": ["-noautorotate"], "-vf": "transpose=1"}
    else:
        ffparams = {}

    decoder = FFdecoder(str(input_video_pathstring), frame_format="bgr24", verbose=False, **ffparams).formulate()
    metadata_dictionary = json.loads(decoder.metadata)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    framerate = metadata_dictionary["output_framerate"]
    framesize = tuple(metadata_dictionary["output_frames_resolution"])

    writer = cv2.VideoWriter(output_video_pathstring, fourcc, framerate, framesize)
    
    current_frame = 0
    written_frames = 0
    for frame in decoder.generateFrame():
        if frame is None:
            break
        if current_frame in frame_list:
            writer.write(frame)
            written_frames += 1
        if written_frames == len(frame_list):
            break
        current_frame += 1

    decoder.terminate()
    writer.release()



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

def _find_minimum_video_duration(video_info_dict: Dict[str, dict], lag_dict: dict) -> float:
    min_duration = min([video_dict["video_duration"] - lag_dict[video_dict["camera_name"]] for video_dict in video_info_dict.values()])
    return min_duration

def _name_synced_video(raw_video_filename: str) -> str:
    raw_video_filename = str(raw_video_filename)
    if raw_video_filename.split("_")[0] == "fr":
        synced_video_name = "synced_" + raw_video_filename[3:] + ".mp4"
    else:
        synced_video_name = "synced_" + raw_video_filename + ".mp4"
    return synced_video_name

def _get_frame_list(start_frame: int, duration_frames: int) -> list:
    return [start_frame + frame for frame in range(duration_frames)]

def trim_videos(
    video_info_dict: Dict[str, dict],
    synchronized_folder_path: Path,
    lag_dict: Dict[str, float],
    fps: float,
    video_handler: str = "deffcode",
) -> list:
    minimum_duration = _find_minimum_video_duration(video_info_dict=video_info_dict, lag_dict=lag_dict)
    minimum_frames = int(minimum_duration * fps)

    for video_dict in video_info_dict.values():
        logger.debug(f"trimming video file {video_dict['camera_name']}")
        synced_video_name = _name_synced_video(raw_video_filename=video_dict["camera_name"])

        start_time = lag_dict[video_dict["camera_name"]]
        start_frame = int(start_time * fps)
        frame_list = _get_frame_list(start_frame=start_frame, duration_frames=minimum_frames)

        logger.info(f"Saving video - cam name: {video_dict['camera_name']}")
        if video_handler == "ffmpeg":            
            logger.info(f"desired saving duration is: {minimum_duration} seconds")
            trim_single_video_ffmpeg(
                input_video_pathstring=video_dict["video_pathstring"],
                start_time=start_time,
                desired_duration=minimum_duration,
                output_video_pathstring=str(synchronized_folder_path / synced_video_name),
            )
            logger.info(f"Video saved - cam name: {video_dict['camera_name']}, video duration in seconds: {minimum_duration}")
        if video_handler == "deffcode":
            logger.info(f"start frame is: {start_frame} desired saving duration is: {minimum_frames} frames")
            trim_single_video_deffcode(
                input_video_pathstring=video_dict["video_pathstring"],
                frame_list=frame_list,
                output_video_pathstring=str(synchronized_folder_path / synced_video_name),
            )
            logger.info(f"Video saved - cam name: {video_dict['camera_name']}, video duration in frames: {minimum_frames}")
            



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

def convert_video_to_mp4(input_video_pathstring: str) -> Path:
    debugpy.debug_this_thread()
    output_video_pathstring = input_video_pathstring.replace(Path(input_video_pathstring).suffix, ".mp4")
    convert_video_subprocess = subprocess.run(
        [
            "ffmpeg",
            "-i",
            input_video_pathstring,
            "-crf",
            "18",
            "-vf",
            "format=yuv420p",
            output_video_pathstring
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return Path(output_video_pathstring)


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