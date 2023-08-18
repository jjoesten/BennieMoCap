import logging
logger = logging.getLogger(__name__)

import toml

from src.data_layer.session_models.session_info_model import SessionInfoModel
from src.system.paths_and_filenames.path_getters import get_most_recent_session_toml_path

def update_most_recent_session_toml(session_info_model: SessionInfoModel):
    output_path = get_most_recent_session_toml_path()
    logger.info(f"Saving most recent session path {str(session_info_model.path)} to toml file: {str(output_path)}")

    toml_dict = {}
    toml_dict["most_recent_session_path"] = str(session_info_model.path)
    toml_dict["session_status"] = session_info_model.status_check

    with open(str(output_path), "w") as file:
        toml.dump(toml_dict, file)