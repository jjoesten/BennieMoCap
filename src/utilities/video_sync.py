import logging
logger = logging.getLogger(__name__)

import time
import toml
import librosa

from pathlib import Path
from typing import List
from matplotlib import pyplot as plt
import numpy as np

from src.system.paths_and_filenames.folder_and_filenames import AUDIO_FOLDER_NAME
from src.utilities.video import get_video_paths, create_video_info_dict, get_fps_list, trim_videos, get_frame_count_of_videos
from src.utilities.audio import extract_audio_files, get_audio_sample_rates, find_lags, remove_audio_files_from_audio_signal_dict, attach_audio_to_videos, get_audio_paths_from_folder
from src.utilities.list import check_list_values_are_equal

AUDIO_NAME = "Audio_information"
RAW_VIDEO_NAME = "Raw_video_information"
SYNCHRONIZED_VIDEO_NAME = "Synchronized_video_information"
LAG_DICTIONARY_NAME = "Lag_dictionary"
DEBUG_TOML_NAME = "synchronization_debug.toml"
DEBUG_PLOT_NAME = "debug_plot.png"
AUDIO_FILES_FOLDER_NAME = "audio_files"
TRIMMED_AUDIO_FOLDER_NAME = "trimmed_audio"

def synchronize_videos_from_audio(
    raw_video_folder_path: Path,
    synchronized_video_folder_path: Path = None,
    file_type: str = ".mp4",
    video_handler: str = "deffcode",
    create_debug_plots_bool: bool = True,
):
    start_timer = time.time()
    
    video_paths_list = get_video_paths(video_folder=raw_video_folder_path)
    if synchronized_video_folder_path is None or not synchronized_video_folder_path.exists():
        Path(synchronized_video_folder_path).mkdir(exist_ok=True, parents=True)
    synchronized_video_folder_path = Path(synchronized_video_folder_path)

    audio_folder_path = synchronized_video_folder_path / AUDIO_FOLDER_NAME
    if not audio_folder_path.exists():
        audio_folder_path.mkdir(exist_ok=True, parents=True)

    # create video and audio dictionaries
    video_info_dict = create_video_info_dict(video_filepath_list=video_paths_list)
    audio_signal_dict = extract_audio_files(video_info_dict=video_info_dict, audio_extension="wav", audio_folder_path=audio_folder_path)

    fps_list = get_fps_list(video_info_dict=video_info_dict)
    audio_sample_rates = get_audio_sample_rates(audio_signal_dict=audio_signal_dict)

    fps = check_list_values_are_equal(input_list=fps_list)
    audio_sample_rate = check_list_values_are_equal(input_list=audio_sample_rates)

    lag_dict = find_lags(audio_signal_dict=audio_signal_dict, sample_rate=audio_sample_rate)

    trim_videos(
        video_info_dict=video_info_dict,
        synchronized_folder_path=synchronized_video_folder_path,
        lag_dict=lag_dict,
        fps=fps,
        video_handler=video_handler
    )            


    synchronized_video_framecounts = get_frame_count_of_videos(folder_path=synchronized_video_folder_path)
    logger.info(f"All videos are {check_list_values_are_equal(synchronized_video_framecounts)} frames long")

    synchronized_videos_info_dict = create_video_info_dict(video_filepath_list=get_video_paths(synchronized_video_folder_path))

    save_dictionaries_to_toml(
        input_dictionaries={
            RAW_VIDEO_NAME: video_info_dict,
            SYNCHRONIZED_VIDEO_NAME: synchronized_videos_info_dict,
            AUDIO_NAME: remove_audio_files_from_audio_signal_dict(audio_signal_dict=audio_signal_dict),
            LAG_DICTIONARY_NAME: lag_dict,
        },
        output_file_path = synchronized_video_folder_path / DEBUG_TOML_NAME
    )

    attach_audio_to_videos(
        synchronized_video_folder_path=synchronized_video_folder_path,
        audio_folder_path=audio_folder_path,
        lag_dictionary=lag_dict,
        synchronized_video_length=next(iter(synchronized_videos_info_dict.values()))["video_duration"],
    )

    if create_debug_plots_bool:
        create_debug_plots(synchronized_video_folder_path=synchronized_video_folder_path)

    end_timer = time.time()
    logger.info(f"Elapsed processing time in seconds: {end_timer - start_timer}")

    return synchronized_video_folder_path


def save_dictionaries_to_toml(input_dictionaries: dict, output_file_path: Path):
    with open(output_file_path, "w") as toml_file:
        toml_file.write(toml.dumps(input_dictionaries))

def create_debug_plots(synchronized_video_folder_path: Path):
    output_filepath = synchronized_video_folder_path / DEBUG_PLOT_NAME
    raw_audio_folder_path = synchronized_video_folder_path / AUDIO_FILES_FOLDER_NAME
    trimmed_audio_folder_path = raw_audio_folder_path / TRIMMED_AUDIO_FOLDER_NAME

    list_raw_audio_paths = get_audio_paths_from_folder(raw_audio_folder_path)
    list_trimmed_audio_paths = get_audio_paths_from_folder(trimmed_audio_folder_path)

    logging.info("Creating audio debug plots")
    plot_waveforms(
        raw_audio_filepath_list=list_raw_audio_paths,
        trimmed_audio_filepath_list=list_trimmed_audio_paths,
        output_filepath=output_filepath
    )

def plot_waveforms(
    raw_audio_filepath_list: List[Path],
    trimmed_audio_filepath_list: List[Path],
    output_filepath: Path
):
    fig, axs = plt.subplots(2, 1, sharex=True, sharey=True)
    fig.suptitle("Audio Cross Correlation Debug")

    axs[0].set_ylabel("Amplitude")
    axs[1].set_ylabel("Amplitude")
    axs[1].set_xlabel("Time (s)")
    
    axs[0].set_title("Before Cross Correlation")
    axs[1].set_title("After Cross Correlation")

    for audio_filepath in raw_audio_filepath_list:
        audio_signal, sr = librosa.load(path=audio_filepath, sr=None)
        time = np.linspace(0, len(audio_signal) / sr, num=len(audio_signal))
        axs[0].plot(time, audio_signal, alpha=0.4)
    for audio_filepath in trimmed_audio_filepath_list:
        audio_signal, sr = librosa.load(path=audio_filepath, sr=None)
        time = np.linspace(0, len(audio_signal) / sr, num=len(audio_signal))
        axs[1].plot(time, audio_signal, alpha=0.4)

    logger.info(f"Saving debug plots to: {output_filepath}")
    plt.savefig(output_filepath)
