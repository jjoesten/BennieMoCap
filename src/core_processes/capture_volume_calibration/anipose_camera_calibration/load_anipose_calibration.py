import logging
logger = logging.getLogger(__name__)

import shutil
import filecmp
from pathlib import Path
from typing import Union

from src.core_processes.capture_volume_calibration.anipose_camera_calibration import anipose_lib
from src.system.paths_and_filenames.path_getters import get_last_successful_calibration_toml_path

def load_anipose_calibration_toml_from_path(
    toml_path: Union[str, Path],
    save_path: Union[str, Path]
):
    logger.info(f"Loading camera calibration from: {str(toml_path)}")
    try:
        anipose_calibration_object = anipose_lib.CameraGroup.load(str(toml_path))
        copy_pathstring = str(Path(save_path) / Path(toml_path).name)

        if Path(copy_pathstring).is_file() and not filecmp.cmp(str(toml_path), copy_pathstring):
            logger.info(f"Saving copy of {toml_path} to {save_path}")
            shutil.copyfile(str(toml_path), copy_pathstring)
        
        return anipose_calibration_object
    except Exception as e:
        logger.error(f"Failed to load anipose calibration info from {str(toml_path)}")
        raise e