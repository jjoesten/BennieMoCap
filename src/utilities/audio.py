import logging
logger = logging.getLogger(__name__)
import subprocess
from pathlib import Path
from typing import Dict, List
import librosa
from scipy import signal
import numpy as np
import tempfile
import shutil
import soundfile as sf

from src.utilities.video import get_video_paths

TRIMMED_AUDIO_FOLDER_NAME = "trimmed_audio"


def extract_audio_files(video_info_dict: Dict[str, dict], audio_extension: str, audio_folder_path: Path) -> dict:
    audio_signal_dict = dict()
    for video_dict in video_info_dict.values():
        extract_audio_from_video_ffmpeg(
            file_pathstring=video_dict["video_pathstring"],
            file_name=video_dict["camera_name"],
            output_folder_path=audio_folder_path,
            output_extension=audio_extension,
        )

        audio_name = video_dict["camera_name"] + "." + audio_extension
        audio_file_path: Path = audio_folder_path / audio_name

        if not audio_file_path.is_file():
            logging.error("Error loading audio file, verify video has audio track")
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        audio_signal, sample_rate = librosa.load(path=audio_file_path, sr=None)

        audio_duration = librosa.get_duration(y=audio_signal, sr=sample_rate)
        logging.info(f"audio file {audio_name} is {audio_duration} seconds long")
        audio_signal_dict[audio_name] = {
            "audio_file": audio_signal,
            "sample_rate": sample_rate,
            "camera_name": video_dict["camera_name"],
            "audio_duration": audio_duration,
        }

    return audio_signal_dict

def extract_audio_from_video_ffmpeg(
    file_pathstring: str,
    file_name: str,
    output_folder_path: Path,
    output_extension: str = "wav",
):
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            file_pathstring,
            f"{output_folder_path}/{file_name}.{output_extension}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

def attach_audio_to_video_ffmpeg(
    input_video_pathstring: str,
    audio_file_pathstring: str,
    output_video_pathstring: str
):
    attach_audio_subprocess = subprocess.run(
        [
            "ffmpeg",
            "-i",
            f"{input_video_pathstring}",
            "-i",
            f"{audio_file_pathstring}",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            f"{output_video_pathstring}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if attach_audio_subprocess.returncode != 0:
        print(f"Error occurred: {attach_audio_subprocess.stderr.decode('utf-8')}")

def get_audio_sample_rates(audio_signal_dict: Dict[str, float]) -> list:
    return [audio_signal["sample_rate"] for audio_signal in audio_signal_dict.values()]

def cross_correlate(audio1, audio2):
    correlation = signal.correlate(audio1, audio2, mode="full", method="fft")
    lags = signal.correlation_lags(audio1.size, audio2.size, mode="full")
    lag = lags[np.argmax(correlation)]
    return lag

def normalize_lag_dictionary(lag_dictionary: Dict[str, float]) -> Dict[str, float]:
    normalized_lag_dictionary = {
        camera_name: (max(lag_dictionary.values()) - value)
        for camera_name, value in lag_dictionary.items()
    }
    return normalized_lag_dictionary

def find_lags(audio_signal_dict: dict, sample_rate: int) -> Dict[str, float]:
    comparison_file_key = next(iter(audio_signal_dict))
    logger.info(f"comparison file is: {comparison_file_key}, sample rate is: {sample_rate}")
    lag_dict = {
        single_audio_dict["camera_name"]: cross_correlate(
            audio1=audio_signal_dict[comparison_file_key]["audio_file"],
            audio2=single_audio_dict["audio_file"],
        )
        / sample_rate
        for single_audio_dict in audio_signal_dict.values()
    }

    normalized_lag_dict = normalize_lag_dictionary(lag_dictionary=lag_dict)

    logger.info(f"original lag dict: {lag_dict} normalized lag dict: {normalized_lag_dict}")

    return normalized_lag_dict

def remove_audio_files_from_audio_signal_dict(audio_signal_dict: dict) -> dict:
    for audio_info_dictionary in audio_signal_dict.values():
        audio_info_dictionary.pop("audio_file")
    return audio_signal_dict

def attach_audio_to_videos(
    synchronized_video_folder_path: Path,
    audio_folder_path: Path,
    lag_dictionary: dict,
    synchronized_video_length: float,
):
    trimmed_audio_folder_path = trim_audio_files(
        audio_folder_path=audio_folder_path,
        lag_dictionary=lag_dictionary,
        synced_video_length=synchronized_video_length
    )

    with tempfile.TemporaryDirectory(dir=str(synchronized_video_folder_path)) as temp_dir:
        for video in get_video_paths(synchronized_video_folder_path):
            video_name = video.stem
            audio_filename = f"{str(video_name).split('_')[-1]}.wav"
            output_video_pathstring = str(Path(temp_dir) / f"{video_name}_with_audio_temp.mp4")

            logger.info(f"Attaching audio to video {video_name}")
            attach_audio_to_video_ffmpeg(
                input_video_pathstring=str(video),
                audio_file_pathstring=str(Path(trimmed_audio_folder_path) / audio_filename),
                output_video_pathstring=output_video_pathstring,
            )

            shutil.move(output_video_pathstring, video)

def get_audio_paths_from_folder(folder_path: Path, file_extension: str = ".wav") -> List[Path]:
    search_extension = "*" + file_extension.lower()
    return Path(folder_path).glob(search_extension)

def trim_audio_files(audio_folder_path: Path, lag_dictionary: dict, synced_video_length: float):
    logger.info("Trimming audio files to match syncronized video length")
    trimmed_audio_folder_path = Path(audio_folder_path) / TRIMMED_AUDIO_FOLDER_NAME
    trimmed_audio_folder_path.mkdir(exist_ok=True, parents=True)

    for audio_filepath in audio_folder_path.glob("*.wav"):
        audio_signal, sr = librosa.load(path=audio_filepath, sr=None)
        lag = lag_dictionary[audio_filepath.stem]
        lag_in_samples = int(float(lag) * sr)
        synced_video_length_in_samples = int(synced_video_length * sr)
        shortened_audio_signal = audio_signal[lag_in_samples:]
        shortened_audio_signal = shortened_audio_signal[:synced_video_length_in_samples]

        audio_filename = str(audio_filepath.stem) + ".wav"

        logger.info(f"Saving audio {audio_filename}")
        output_path = trimmed_audio_folder_path / audio_filename
        sf.write(output_path, shortened_audio_signal, sr, subtype="PCM_24")

    return trimmed_audio_folder_path