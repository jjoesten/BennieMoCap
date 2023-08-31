import logging
logger = logging.getLogger(__name__)

import json
from pathlib import Path
from typing import Union, Dict, Any
import numpy as np
import pandas as pd

from src.core_processes.processing_2d.mediapipe.data_models.mediapipe_skeleton_names_and_connections import mediapipe_skeleton_schema
from src.core_processes.post_process_skeleton.center_of_mass import BODY_SEGMENT_NAMES
from src.data_layer.data_models import FrameData, Timestamps, Point, SkeletonSchema
from src.system.paths_and_filenames.folder_and_filenames import (
    MEDIAPIPE_BODY_3D_DATAFRAME_CSV_FILENAME,
    MEDIAPIPE_RIGHT_HAND_3D_DATAFRAME_CSV_FILENAME,
    MEDIAPIPE_LEFT_HAND_3D_DATAFRAME_CSV_FILENAME,
    MEDIAPIPE_FACE_3D_DATAFRAME_CSV_FILENAME,
    MEDIAPIPE_SKELETON_SEGMENT_LENGTHS_JSON_FILENAME,
    MEDIAPIPE_NAMES_AND_CONNECTIONS_JSON_FILENAME
)
from src.system.paths_and_filenames.path_getters import (
    get_output_data_folder_path,
    get_timestamps_folder_path,
    get_total_body_center_of_mass_file_path,
    get_segment_center_of_mass_file_path,
    get_full_npy_file_path
)


class DataLoader():
    def __init__(
        self,
        session_folder_path: Union[str, Path],
        include_hands: bool = True,
        include_face: bool = True,
    ):
        self._session_folder_path = Path(session_folder_path)
        self._session_name = self._session_folder_path.name
        self._output_folder_path = Path(get_output_data_folder_path(self._session_folder_path))
        self._include_hands = include_hands
        self._include_face = include_face

        self._load_data()

    def _load_data(self):
        self._load_timestamps()
        self._load_data_frames()
        self._load_full_npy_data()
        self._load_com_data()
        self._load_segment_lengths()
        self._load_names_and_connections()
        self._load_skeleton_schema()
        self._validate_data()

    def _load_timestamps(self):
        timestamps_path = get_timestamps_folder_path(self._session_folder_path)
        if timestamps_path is None:
            logger.warning("No timestamps directory found. Skipping timestamp loading")
            return
        
        timestamps_by_camera = {}
        for timestamps_npy in Path(timestamps_path).glob("*.npy"):
            camera_name = timestamps_npy.stem
            timestamps_by_camera[camera_name] = np.load(str(timestamps_npy))

        self._timestamps_by_camera = timestamps_by_camera
        timestamps = [timestamps for timestamps in timestamps_by_camera.values()]
        self._timestamps_mean_per_frame = np.nanmean(np.asarray(timestamps), axis=0)

    def _load_data_frames(self):
        self.body_dataframe = self._load_dataframe(MEDIAPIPE_BODY_3D_DATAFRAME_CSV_FILENAME)
        self._number_frames = len(self.body_dataframe)
        if self._include_hands:
            self._right_hand_dataframe = self._load_dataframe(MEDIAPIPE_RIGHT_HAND_3D_DATAFRAME_CSV_FILENAME)
            self._left_hand_dataframe = self._load_dataframe(MEDIAPIPE_LEFT_HAND_3D_DATAFRAME_CSV_FILENAME)
        if self._include_face:
            self._face_dataframe = self._load_dataframe(MEDIAPIPE_FACE_3D_DATAFRAME_CSV_FILENAME)

    def _load_dataframe(self, filename):
        return pd.read_csv(self._output_folder_path / filename)
    
    def _load_full_npy_data(self):
        self._data_frame_name_xyz = np.load(get_full_npy_file_path(output_data_folder=self._output_folder_path))

    def _load_com_data(self):
        self._center_of_mass_xyz = np.load(get_total_body_center_of_mass_file_path(output_data_folder=self._output_folder_path))
        self._segment_center_of_mass_xyz = np.load(get_segment_center_of_mass_file_path(output_dat_folder=self._output_folder_path))

    def _load_segment_lengths(self):
        with open(self._output_folder_path / MEDIAPIPE_SKELETON_SEGMENT_LENGTHS_JSON_FILENAME, "r") as file:
            self._segment_lengths = json.loads(file.read())

    def _load_names_and_connections(self):
        with open(self._output_folder_path / MEDIAPIPE_NAMES_AND_CONNECTIONS_JSON_FILENAME, "r") as file:
            self._names_and_connections = json.loads(file.read())

    def _load_skeleton_schema(self):
        self._skeleton_schema = SkeletonSchema(schema_dict=mediapipe_skeleton_schema)

    def _validate_data(self):
        self._validate_dataframe(self._right_hand_dataframe, "right hand")
        self._validate_dataframe(self._left_hand_dataframe, "left hand")
        self._validate_dataframe(self._face_dataframe, "face")
        self._validate_numpy_array(self._center_of_mass_xyz, "center of mass")
        self._validate_numpy_array(self._segment_center_of_mass_xyz, "segment center of mass")

    def _validate_dataframe(self, df, df_name):
        if df is not None and len(df) != self._number_frames:
            raise ValueError(f"The numver of frames in the {df_name} dataframe is not the same as the number of frames in tehe body dataframe.")
        
    def _validate_numpy_array(self, np_array, np_array_name):
        if np_array is not None and np_array.shape[0] != self._number_frames:
            raise ValueError(f"The number of frames in the {np_array} data is not the same as the number of frames in the body dataframe.")

    def _load_frame_data(self, frame_number: int) -> FrameData:
        return FrameData(timestamps=self._get_timestamps(frame_number), tracked_points=self._get_tracked_points(frame_number))
    
    def _get_timestamps(self, frame_number: int):
        try:
            return Timestamps(
                mean=self._timestamps_mean_per_frame[frame_number], 
                by_camera={camera_name: timestamps[frame_number] for camera_name, timestamps in self._timestamps_by_camera.items()}
            )
        except AttributeError:
            return Timestamps()
        
    def _get_tracked_points(self, frame_number: int) -> Dict[str, Point]:
        right_hand_points = {}
        left_hand_points = {}
        face_points = {}

        body_points = self._process_dataframe(self.body_dataframe.iloc[frame_number, :])
        com_points = self._get_com_data(frame_number)

        if self._include_hands:
            left_hand_points, right_hand_points = self._load_hand_data(frame_number)
        if self._include_face:
            face_points = self._process_dataframe(self._face_dataframe.iloc[frame_number, :])

        all_points = {}
        all_points.update(body_points)
        all_points.update(com_points)
        all_points.update(right_hand_points)
        all_points.update(left_hand_points)
        all_points.update(face_points)

        return all_points
    
    def _load_hand_data(self, frame_number: int):
        right_hand_points = self._process_dataframe(self._right_hand_dataframe.iloc[frame_number, :])
        left_hand_points = self._process_dataframe(self._left_hand_dataframe.iloc[frame_number, :])
        return left_hand_points, right_hand_points
    
    def _get_com_data(self, frame_number: int):
        com_data = {}
        com_data["full_body_com"] = Point(
            x=self._center_of_mass_xyz[frame_number, 0],
            y=self._center_of_mass_xyz[frame_number, 1],
            z=self._center_of_mass_xyz[frame_number, 2],
        )

        for segment_number, segment_name in enumerate(BODY_SEGMENT_NAMES):
            com_data[segment_name] = Point(
                x=self._segment_center_of_mass_xyz[frame_number, segment_number, 0],
                y=self._segment_center_of_mass_xyz[frame_number, segment_number, 1],
                z=self._segment_center_of_mass_xyz[frame_number, segment_number, 2],
            )

        return com_data
    
    def _process_dataframe(self, df) -> Dict[str, Any]:
        tracked_points = {}
        column_names = list(df.index)
        for column_name in column_names:
            point_name = column_name[:-2]
            dimension = column_name[-1]
            value = df[column_name]
            if pd.isna(value):
                value = None

            tracked_points.setdefault(point_name, {})[dimension] = value

        return tracked_points

    def get_data_by_frame(self) -> dict:
        session_data_by_frame_number = {}
        for frame_number in range(self._number_frames):
            session_data_by_frame_number[frame_number] = self._load_frame_data(frame_number).to_dict()
        return session_data_by_frame_number
    
