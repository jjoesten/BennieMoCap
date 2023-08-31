import logging
logger = logging.getLogger(__name__)

import numpy as np
from pathlib import Path
from typing import Union

from src.data_layer.session_models.post_processing_parameter_models import PostProcessingParameterModel

from src.core_processes.capture_volume_calibration.triangulate_3d_data import save_mediapipe_3d_data_to_npy
from src.utilities.geometry import project_3d_data_to_z_plane

from skellyforge.freemocap_utils.postprocessing_widgets.task_worker_thread import TaskWorkerThread
from skellyforge.freemocap_utils.config import default_settings
from skellyforge.freemocap_utils.constants import (
    TASK_FILTERING,
    PARAM_CUTOFF_FREQUENCY,
    PARAM_SAMPLING_RATE,
    PARAM_ORDER,
    PARAM_ROTATE_DATA,
    TASK_SKELETON_ROTATION,
    TASK_INTERPOLATION,
    TASK_FINDING_GOOD_FRAME
)

class PostProcessedDataHandler:
    def __init__(self):
        self.processed_skeleton = None
    
    def data_callback(self, processed_skeleton: np.ndarray):
        self.processed_skeleton = processed_skeleton

def save_skeleton_array_to_npy(
        array_to_save: np.ndarray,
        skeleton_file_name: Union[str, Path],
        save_folder: Union[str, Path]
):
    if not str(skeleton_file_name).endswith(".npy"):
        skeleton_file_name += ".npy"
    Path(save_folder).mkdir(parents=True, exist_ok=True)
    np.save(str(Path(save_folder) / skeleton_file_name), array_to_save)

def post_process_data(session_processing_parameter_model: PostProcessingParameterModel, raw_skel3d_frame_marker_xyz: np.ndarray):
    filter_sampling_rate = session_processing_parameter_model.post_processing_parameters_model.framerate
    filter_cutoff_frequency = session_processing_parameter_model.post_processing_parameters_model.butterworth_filter_parameters.cutoff_frequency
    filter_order = session_processing_parameter_model.post_processing_parameters_model.butterworth_filter_parameters.order
    
    adjusted_settings = adjust_default_settings(filter_sampling_rate, filter_cutoff_frequency, filter_order)
    
    processed_skeleton = run_post_processing_worker(raw_skel3d_frame_marker_xyz=raw_skel3d_frame_marker_xyz, settings_dictionary=adjusted_settings)
    return processed_skeleton


def adjust_default_settings(filter_sampling_rate, filter_cutoff_frequency, filter_order):
    adjusted_settings = default_settings.copy()
    adjusted_settings[TASK_FILTERING][PARAM_CUTOFF_FREQUENCY] = filter_cutoff_frequency
    adjusted_settings[TASK_FILTERING][PARAM_SAMPLING_RATE] = filter_sampling_rate
    adjusted_settings[TASK_FILTERING][PARAM_ORDER] = filter_order
    adjusted_settings[TASK_FILTERING][PARAM_ROTATE_DATA] = False
    return adjusted_settings
    
def run_post_processing_worker(raw_skel3d_frame_marker_xyz: np.ndarray, settings_dictionary: dict):
    def handle_thread_finished(results, post_processed_data_handler: PostProcessedDataHandler):
        processed_skeleton = results[TASK_FILTERING]["result"]
        post_processed_data_handler.data_callback(processed_skeleton=processed_skeleton)

    task_list = [TASK_INTERPOLATION, TASK_FILTERING, TASK_FINDING_GOOD_FRAME, TASK_SKELETON_ROTATION]
    post_processed_data_handler = PostProcessedDataHandler()

    logger.info("Starting post-processing worker thread")

    worker_thread = TaskWorkerThread(
        raw_skeleton_data=raw_skel3d_frame_marker_xyz,
        task_list=task_list,
        settings=settings_dictionary,
        all_tasks_finished_callback=lambda results: handle_thread_finished(results, post_processed_data_handler)
    )
    worker_thread.start()
    worker_thread.join()
    logger.info("Post processing done")

    return post_processed_data_handler.processed_skeleton

def process_single_camera_skeleton_data(
    input_image_data_frame_marker_xyz: np.ndarray,
    raw_data_folder_path: Union[str, Path],
    project_to_z_plane: bool = True
) -> [np.ndarray, np.ndarray]:
    # TODO: project to a plane other than Z. For now just Z
    logger.info("Single camera detected - Altering 3d data to resemble mulit-camera data")

    skeleton_reprojection_error = np.zeros(input_image_data_frame_marker_xyz.shape[0:2])
    raw_skel3d = project_3d_data_to_z_plane(skel3d=input_image_data_frame_marker_xyz)

    save_mediapipe_3d_data_to_npy(
        data3d=raw_skel3d,
        reprojection_error=skeleton_reprojection_error,
        save_path=raw_data_folder_path
    )

    return raw_skel3d, skeleton_reprojection_error