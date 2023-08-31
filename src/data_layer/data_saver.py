import logging
logger = logging.getLogger(__name__)

import json
from pathlib import Path
from typing import Union
import numpy as np
import pandas as pd
from typing import Any, Dict

from src.data_layer.data_loader import DataLoader
from src.data_layer.data_models import InfoDict

class DataSaver:
    def __init__(self, session_folder_path: Union[str, Path], include_hands: bool = True, include_face: bool = True):
        self._session_folder_path = Path(session_folder_path)
        self._session_name = self._session_folder_path.name

        self._data_loader = DataLoader(session_folder_path=self._session_folder_path, include_hands=include_hands, include_face=include_face)

        self._data_by_frame = None
        self._number_frames = None

    def save_all(self):
        self._data_by_frame = self._data_loader.get_data_by_frame()
        self._save_to_json()
        self._save_to_csv()
        self._save_to_npy()

    def _save_to_json(self, save_path: Union[str, Path] = None):
        dict_to_save = {}
        dict_to_save["info"] = self._get_info_dict().dict()
        dict_to_save["data_by_frame"] = self._data_by_frame

        if save_path is None:
            save_path = self._session_folder_path / f"{self._session_name}_by_frame.json"

        save_path.write_text(json.dumps(dict_to_save, indent=4), encoding="utf-8")
        logger.info(f"Session data saved to {save_path}")

    def _save_to_csv(self, save_path: Union[str, Path]):
        df_data = []
        for frame_data in self._data_by_frame.values():
            df_data.append(self._generate_frame_data_row(frame_data))

        df = pd.DataFrame(df_data)

        if save_path is None:
            save_path = self._session_folder_path / f"{self._session_name}_by_trajectory.csv"
        
        df.to_csv(save_path, index=False)
        logger.info(f"Session data saved to {save_path}")

    def _save_to_npy(self, save_path: Union[str, Path]):
        if save_path is None:
            save_path = self._session_folder_path / f"{self._session_name}_frame_name_xyz.npy"
        np.save(save_path, self._data_loader.data_frame_name_xyz)
        logger.info(f"Saved session data to {save_path}")
        

    def _generate_frame_data_row(self, frame_data: Dict[str, Any]) -> Dict:
        frame_data_row = {}
        frame_data_row["timestamp"] = frame_data["timestamps"]["mean"]
        frame_data_row["timestamp_by_camera"] = str(frame_data["timestamps"]["by_camera"])

        for key, tracked_point in frame_data["tracked_points"].items():
            frame_data_row[f"{key}_x"] = tracked_point["x"]
            frame_data_row[f"{key}_y"] = tracked_point["y"]
            frame_data_row[f"{key}_z"] = tracked_point["z"]

        return frame_data_row
    
    def _get_info_dict(self):
        return InfoDict(
            segment_lengths=self._data_loader.segment_lengths,
            schemas=[self._data_loader.skeleton_schema.dict()]
        )
