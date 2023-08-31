import logging
logger = logging.getLogger(__name__)

import multiprocessing
from pathlib import Path
import numpy as np
import pandas as pd

from src.core_processes.capture_volume_calibration.anipose_camera_calibration.load_anipose_calibration import load_anipose_calibration_toml_from_path
from src.core_processes.capture_volume_calibration.triangulate_3d_data import triangulate_3d_data
from src.core_processes.post_process_skeleton.center_of_mass import run_center_of_mass_calculations
from src.core_processes.post_process_skeleton.estimate_skeleton_segment_lengths import (
    estimate_skeleton_segment_lengths,
    mediapipe_skeleton_segment_definitions
)
from src.core_processes.post_process_skeleton.post_process_skeleton import (
    post_process_data,
    save_skeleton_array_to_npy,
    process_single_camera_skeleton_data
)
from src.core_processes.processing_2d.mediapipe.convert_mediapipe_npy_to_csv import convert_mediapipe_npy_to_csv
from src.core_processes.processing_2d.mediapipe.mediapipe_skeleton_detector import MediapipeSkeletonDetector

from src.core_processes.processing_2d.mediapipe.data_models.mediapipe_skeleton_names_and_connections import mediapipe_names_and_connections_dict

from src.data_layer.data_saver import DataSaver
from src.data_layer.session_models.post_processing_parameter_models import PostProcessingParameterModel

from src.system.logging.configure import log_view_format_string
from src.system.logging.queue_logger import DirectQueueHandler

from src.system.paths_and_filenames.folder_and_filenames import (
    RAW_DATA_FOLDER_NAME,
    CENTER_OF_MASS_FOLDER_NAME,
    SEGMENT_CENTER_OF_MASS_NPY_FILENAME,
    TOTAL_BODY_CENTER_OF_MASS_NPY_FILENAME,
    MEDIAPIPE_BODY_3D_DATAFRAME_CSV_FILENAME,
    MEDIAPIPE_SKELETON_SEGMENT_LENGTHS_JSON_FILENAME,
    MEDIAPIPE_NAMES_AND_CONNECTIONS_JSON_FILENAME,
    MEDIAPIPE_3D_NPY_FILENAME
)

from src.tests.test_image_tracking_data_shape import test_image_tracking_data_shape
from src.tests.test_mediapipe_skeleton_data_shape import test_mediapipe_skeleton_data_shape

from src.utilities.geometry import rotate_90_degrees_around_x_axis
from src.utilities.dict import save_dictionary_to_json





def process_session_folder(
    session_processing_parameter_model: PostProcessingParameterModel,
    kill_event: multiprocessing.Event = None,
    queue: multiprocessing.Queue = None,
    use_tqdm: bool = True
):
    if queue:
        handler = DirectQueueHandler(queue)  
        handler.setFormatter(logging.Formatter(fmt=log_view_format_string, datefmt="%Y-%m-%dT%H:%M:%S"))
        logger.addHandler(handler)

    session = session_processing_parameter_model

    if not Path(session.session_info_model.synchronized_videos_folder_path).exists():
        raise FileNotFoundError(f"Could not find synchronized_videos folder at {session.session_info_model.synchronized_videos_folder_path}")
    
    # 2D image tracking
    if session.mediapipe_parameters_model.skip_2d_image_tracking:
        logger.info(f"Skipping 2D skeleton detection and loading data from: {session.session_info_model.mediapipe_2d_data_npy_file_path}")
        try:
            mediapipe_image_data_numCams_numFrames_numTrackedPts_XYZ = np.load(session.session_info_model.mediapipe_2d_data_npy_file_path)
        except Exception as e:
            logger.error(e)
            logger.error("Failed to load 2D data, cannot continue processing", exc_info=True)
            return
    else:
        logger.info("Detecting 2D skeletons")
        mediapipe_skeleton_detector = MediapipeSkeletonDetector(parameter_model=session.mediapipe_parameters_model, use_tqdm=use_tqdm)

        mediapipe_image_data_numCams_numFrames_numTrackedPts_XYZ = (
            mediapipe_skeleton_detector.process_folder(
                video_folder_path=session.session_info_model.synchronized_videos_folder_path,
                output_data_folder_path=session.session_info_model.output_data_folder_path / RAW_DATA_FOLDER_NAME
            )
        )

    if kill_event is not None and kill_event.is_set():
        return
    
    try:
        assert test_image_tracking_data_shape(
            synchronized_video_folder_path=session.session_info_model.synchronized_videos_folder_path,
            image_tracking_data_file_path=session.session_info_model.mediapipe_2d_data_npy_file_path,
        )
    except AssertionError as e:
        logger.error(e, exc_info=True)


    # 3D skeleton triangulation

    # fake 3d data if single camera
    if mediapipe_image_data_numCams_numFrames_numTrackedPts_XYZ.shape[0] == 1:
        (raw_skel3d_frame_marker_xyz, skeleton_reprojection_error_fr_mar) = process_single_camera_skeleton_data(
            input_image_data_frame_marker_xyz=mediapipe_image_data_numCams_numFrames_numTrackedPts_XYZ[0],
            raw_data_folder_path=Path(session.session_info_model.raw_data_folder_path)
        )
    else:
        if session.anipose_triangulate_3d_parameters_model.skip_3d_triangulation:
            logger.info(f"Skipping 3D triangulation, loading data from {session.session_info_model.raw_mediapipe_3d_data_npy_file_path}")
            raw_skel3d_frame_marker_xyz = np.load(session.session_info_model.raw_mediapipe_3d_data_npy_file_path)
            skeleton_reprojection_error_fr_mar = np.load(session.session_info_model.mediapipe_reprojection_error_data_npy_file_path)
        else:
            logger.info("Triangulating 3D skeletons...")

            assert (session.session_info_model.calibration_toml_check), f"No calibration file found at: {session.session_info_model.calibration_toml_path}"
            assert (session.session_info_model.data2d_status_check), f"No mediapipe 2D data found at: {session.session_info_model.mediapipe_2d_data_npy_file_path}"

            anipose_calibration_object = load_anipose_calibration_toml_from_path(
                camera_calibration_data_toml_path=session.session_info_model.calibration_toml_path,
                save_copy_of_calibration_data_path=session.session_info_model.path
            )

            (
                raw_skel3d_frame_marker_xyz, 
                skeleton_reprojection_error_fr_mar
            ) = triangulate_3d_data(
                anipose_calibration_object=anipose_calibration_object,
                mediapipe_2d_data=mediapipe_image_data_numCams_numFrames_numTrackedPts_XYZ[:, :, :, :2],
                output_data_folder_path=session.session_info_model.raw_data_folder_path,
                mediapipe_confidence_cutoff_threshold=session.anipose_triangulate_3d_parameters_model.confidence_threshold_cutoff,
                use_triangulate_ransac=session.anipose_triangulate_3d_parameters_model.use_triangulate_ransac_method,
                kill_event=kill_event
            )

    if kill_event is not None and kill_event.is_set():
        return
    
    try:
        assert test_mediapipe_skeleton_data_shape(
            synchronized_video_folder_path=session.session_info_model.synchronized_videos_folder_path,
            raw_skeleton_npy_file_path=session.session_info_model.raw_mediapipe_3d_data_npy_file_path,
            reprojection_error_file_path=session.session_info_model.mediapipe_reprojection_error_data_npy_file_path,
        )
    except AssertionError as e:
        logger.error(e, exc_info=True)

    logger.info("Using SkellyForge Post-Processing to clean up data...")

    rotated_raw_ske3d_frame_marker_xyz = rotate_90_degrees_around_x_axis(raw_skel3d_frame_marker_xyz)

    skel3d_frame_marker_xyz = post_process_data(
        session_processing_parameter_model=session_processing_parameter_model,
        raw_skel3d_frame_marker_xyz=rotated_raw_ske3d_frame_marker_xyz,
    )

    save_folder_path = session.session_info_model.output_data_folder_path

    logger.info("Saving post processed data")
    save_skeleton_array_to_npy(
        skeleton_array=skel3d_frame_marker_xyz,
        skeleton_filename=MEDIAPIPE_3D_NPY_FILENAME,
        save_folder_path=save_folder_path
    )

    segment_COM_frame_imgPoint_XYZ, totalBodyCOM_frame_XYZ = run_center_of_mass_calculations(skel3d_frame_marker_xyz)

    logger.info("Saving segment COM data")
    save_skeleton_array_to_npy(
        skeleton_array=segment_COM_frame_imgPoint_XYZ,
        skeleton_filename=SEGMENT_CENTER_OF_MASS_NPY_FILENAME,
        save_folder_path=save_folder_path / CENTER_OF_MASS_FOLDER_NAME
    )

    logger.info("Saving total body COM data")
    save_skeleton_array_to_npy(
        skeleton_array=totalBodyCOM_frame_XYZ,
        skeleton_filename=TOTAL_BODY_CENTER_OF_MASS_NPY_FILENAME,
        save_folder_path=save_folder_path / CENTER_OF_MASS_FOLDER_NAME
    )

    try:
        test_mediapipe_skeleton_data_shape(
            synchronized_video_folder_path=session.session_info_model.synchronized_videos_folder_path,
            raw_skeleton_npy_file_path=session.session_info_model.mediapipe_3d_data_npy_file_path,
            reprojection_error_file_path=session.session_info_model.mediapipe_reprojection_error_data_npy_file_path,
        )
    except AssertionError as e:
        logger.error(e, exc_info=True)

    logger.info("Reducing 'npy' data and converting to '.csv'...")
    convert_mediapipe_npy_to_csv(
        mediapipe_3d_frame_trackedPoint_xyz=skel3d_frame_marker_xyz,
        output_data_folder_path=session.session_info_model.output_data_folder_path
    )

    path_to_skeleton_body_csv = session.session_info_model.output_data_folder_path / MEDIAPIPE_BODY_3D_DATAFRAME_CSV_FILENAME
    skeleton_df = pd.read_csv(path_to_skeleton_body_csv)

    logger.info("Estimating skeleton segment lengths...")
    skeleton_segment_lengths_dict = estimate_skeleton_segment_lengths(
        skeleton_df = skeleton_df,
        skeleton_segment_definitions = mediapipe_skeleton_segment_definitions
    )

    save_dictionary_to_json(
        save_path=session.session_info_model.output_data_folder_path,
        filename=MEDIAPIPE_SKELETON_SEGMENT_LENGTHS_JSON_FILENAME,
        dictionary=skeleton_segment_lengths_dict
    )

    save_dictionary_to_json(
        save_path=session.session_info_model.output_data_folder_path,
        filename=MEDIAPIPE_NAMES_AND_CONNECTIONS_JSON_FILENAME,
        dictionary=mediapipe_names_and_connections_dict
    )

    # TODO: Move this method above and deprecate the above methods...
    DataSaver(session_folder_path=session.session_info_model.path).save_all()

    logger.info(f"Done processing {session.session_info_model.path}")




