import logging
logger = logging.getLogger(__name__)

import multiprocessing
from pathlib import Path
import numpy as np
import pandas as pd

from src.system.logging.queue_logger import DirectQueueHandler
from src.system.logging.configure import log_view_format_string

from src.data_layer.session_models.post_processing_parameter_models import PostProcessingParameterModel

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
        # TODO: HERE!!!