import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from typing import Union
import numpy as np
import multiprocessing

from src.core_processes.capture_volume_calibration.anipose_camera_calibration.anipose_lib import CameraGroup

from src.system.paths_and_filenames.folder_and_filenames import (
    RAW_MEDIAPIPE_3D_NPY_FILENAME,
    MEDIAPIPE_REPROJECTION_ERROR_NPY_FILENAME
)


def triangulate_3d_data(
    anipose_calibration_object: CameraGroup,
    mediapipe_2d_data: np.ndarray,
    output_data_folder_path: Union[str, Path],
    mediapipe_confidence_cutoff_threshold: float,
    use_triangulate_ransac: bool = False,
    kill_event: multiprocessing.Event = None
):
    number_cameras = mediapipe_2d_data.shape[0]
    number_frames = mediapipe_2d_data.shape[1]
    number_tracked_points = mediapipe_2d_data[2]
    number_spatial_dimensions = mediapipe_2d_data[3]

    if not number_spatial_dimensions == 2:
        logger.error(f"Should be 2D data, but mediapipe array has {number_spatial_dimensions} spatial dimensions")
        raise Exception
    
    # TODO: Removed 2d data confidence thresholding
    # mediapipe_2d_data = threshold_by_confidence(
    #     data2d=mediapipe_2d_data,
    #     confidence_threshold=mediapipe_confidence_cutoff_threshold
    # )
    
    # reshape to collapse across frames [number_cameras, number_tracked_points(number_frames*number_tracked_points), XY]
    data2d_flat = mediapipe_2d_data.reshape(number_cameras, -1, 2)

    logger.info(
        f"Reconstructing 3d points from 2d points with shape: \n"
        f"number_cameras: {number_cameras}\n"
        f"number_frames: {number_frames}\n"
        f"number_tracked_points: {number_tracked_points}\n"
        f"number_spatial_dimensions: {number_spatial_dimensions}"
    )

    if use_triangulate_ransac:
        logger.info("Using 'triangulate_ransac' method")
        data3d_flat = anipose_calibration_object.triangulate_ransac(data2d_flat, progress=True, kill_event=kill_event)
    else:
        logger.info("Using simple 'triangulate' method")
        data3d_flat = anipose_calibration_object.triangulate(data2d_flat, progress=True, kill_event=kill_event)
    spatial_data3d_numFrames_numTrackedPoints_XYZ_og = data3d_flat.reshape(number_frames, number_tracked_points, 3)

    data3d_reprojectionError_flat = anipose_calibration_object.reprojection_error(data3d_flat, data2d_flat, mean=True)
    data3d_reprojection_error_numFrames_numTrackedPoints = data3d_reprojectionError_flat.reshape(number_frames, number_tracked_points)

    spatial_data3d_numFrames_numTrackedPoints_XYZ = remove_3d_data_with_high_reprojection_error(
        data3d = spatial_data3d_numFrames_numTrackedPoints_XYZ_og,
        reprojection_error = data3d_reprojection_error_numFrames_numTrackedPoints
    )

    save_mediapipe_3d_data_to_npy(
        data3d = spatial_data3d_numFrames_numTrackedPoints_XYZ,
        reprojection_error = data3d_reprojection_error_numFrames_numTrackedPoints,
        save_path = output_data_folder_path
    )

    return (
        spatial_data3d_numFrames_numTrackedPoints_XYZ,
        data3d_reprojection_error_numFrames_numTrackedPoints
    )

def save_mediapipe_3d_data_to_npy(
    data3d: np.ndarray,
    reprojection_error: np.ndarray,
    save_path: Union[str, Path]
):
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)
    
    data3d_save_path = save_path / RAW_MEDIAPIPE_3D_NPY_FILENAME
    logger.info(f"Saving: {data3d_save_path}")
    np.save(str(data3d_save_path), data3d)

    reprojection_error_save_path = save_path / MEDIAPIPE_REPROJECTION_ERROR_NPY_FILENAME
    logger.info(f"Saving {reprojection_error_save_path}")
    np.save(str(reprojection_error_save_path), reprojection_error)

def threshold_by_confidence(
    data2d: np.ndarray,
    confidence_threshold: float = 0.0
):
    data2d[data2d <= confidence_threshold] = np.nan
    number_nans = np.sum(np.isnan(data2d))
    number_points = np.prod(data2d.shape)
    percentage_nans = (np.sum(np.isnan(data2d)) / number_points) * 100
    logger.info(f"After confidence thresholding 'mediapipe_2d' with a confidence threshold of {confidence_threshold}, it has {number_nans} NaN values out of {number_points} ({percentage_nans} %)")
    return data2d

def remove_3d_data_with_high_reprojection_error(
    data3d: np.ndarray,
    reprojection_error: np.ndarray
):
    return data3d
    # TODO: Fix this function, causing over filtering in conjunction with anipose calibration confidence threshold

    logger.info("Removing 3D data with high reprojection error")
    mean_reprojection_error_per_frame = np.nanmean(data3d, axis=1)

    reprojection_error_mean = np.nanmean(mean_reprojection_error_per_frame)
    reprojection_error_median = np.nanmedian(mean_reprojection_error_per_frame)
    reprojection_error_std = np.nanstd(mean_reprojection_error_per_frame)

    median_absolute_deviation = np.nanmedian(np.abs(mean_reprojection_error_per_frame - reprojection_error_median))

    logger.info(f"\nInitial reprojection error - \nmean: {reprojection_error_mean:.3f}, \nstd: {reprojection_error_std:.3f}, \nmedian: {reprojection_error_median:.3f}, \nmedian abs deviation: {median_absolute_deviation:.3f}")

    error_threshold = reprojection_error_median + 3 * median_absolute_deviation

    number_nans_before_thresholding = np.sum(np.isnan(data3d))

    # replace points with high reprojection error
    data3d[reprojection_error > error_threshold] = np.nan

    number_nans_after_thresholding = np.sum(np.isnan(data3d))
    percentage_nans_removed = ((number_nans_before_thresholding - number_nans_after_thresholding) / number_nans_before_thresholding) * 100

    logger.info(f"Removing points with reprojection errror > {error_threshold:.3f}")
    logger.info(f"Number NaNs before thresholding: {number_nans_before_thresholding}")
    logger.info(f"Number NaNs after thresholding: {number_nans_after_thresholding} ({percentage_nans_removed:.2f} %)")

    return data3d