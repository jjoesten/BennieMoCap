import logging
logger = logging.getLogger(__name__)

from typing import List
from rich.progress import track
import numpy as np
import pandas as pd

from src.core_processes.processing_2d.mediapipe.data_models.mediapipe_skeleton_names_and_connections import mediapipe_body_landmark_names

BODY_SEGMENT_NAMES = [
    "head",
    "trunk",
    "right_upper_arm",
    "left_upper_arm",
    "right_forearm",
    "left_forearm",
    "right_hand",
    "left_hand",
    "right_thigh",
    "left_thigh",
    "right_shin",
    "left_shin",
    "right_foot",
    "left_foot",
]

JOINT_CONNECTIONS = [
    ["left_ear", "right_ear"],
    ["mid_chest_marker", "mid_hip_marker"],
    ["right_shoulder", "right_elbow"],
    ["left_shoulder", "left_elbow"],
    ["right_elbow", "right_wrist"],
    ["left_elbow", "left_wrist"],
    ["right_wrist", "right_hand_marker"],
    ["left_wrist", "left_hand_marker"],
    ["right_hip", "right_knee"],
    ["left_hip", "left_knee"],
    ["right_knee", "right_ankle"],
    ["left_knee", "left_ankle"],
    ["right_back_of_foot_marker", "right_foot_index"],
    ["left_back_of_foot_marker", "left_foot_index"],
]

SEGMENT_COM_LENGTHS = [
    0.5,
    0.5,
    0.436,
    0.436,
    0.430,
    0.430,
    0.506,
    0.506,
    0.433,
    0.433,
    0.433,
    0.433,
    0.5,
    0.5,
]

SEGMENT_COM_PERCENTAGES = [
    0.081,
    0.497,
    0.028,
    0.028,
    0.016,
    0.016,
    0.006,
    0.006,
    0.1,
    0.1,
    0.0465,
    0.0465,
    0.0145,
    0.0145,
]

def mediapipe_body_names_match(mediapipe_body_landmark_names: List[str]) -> bool:
    """
    Check if the mediapipe folks have changed their landmark names. If they have, then this function may need to be updated.

    Args:
        mediapipe_body_landmark_names: List of strings, each string is the name of a mediapipe landmark.

    Returns:
        bool: True if the mediapipe landmark names are as expected, False otherwise.
    """
    expected_mediapipe_body_landmark_names = [
        "nose",
        "left_eye_inner",
        "left_eye",
        "left_eye_outer",
        "right_eye_inner",
        "right_eye",
        "right_eye_outer",
        "left_ear",
        "right_ear",
        "mouth_left",
        "mouth_right",
        "left_shoulder",
        "right_shoulder",
        "left_elbow",
        "right_elbow",
        "left_wrist",
        "right_wrist",
        "left_pinky",
        "right_pinky",
        "left_index",
        "right_index",
        "left_thumb",
        "right_thumb",
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle",
        "left_heel",
        "right_heel",
        "left_foot_index",
        "right_foot_index",
    ]
    return mediapipe_body_landmark_names == expected_mediapipe_body_landmark_names

def build_anthropometric_dataframe() -> pd.DataFrame:
    df = pd.DataFrame(
        list(
            zip(
                BODY_SEGMENT_NAMES,
                JOINT_CONNECTIONS,
                SEGMENT_COM_LENGTHS,
                SEGMENT_COM_PERCENTAGES
            )
        ),
        columns=[
            "Segment_Name",
            "Joint_Connection",
            "Segment_COM_Length",
            "Segment_COM_Percentage"
        ],
    )
    df = df.set_index("Segment_Name")
    return df

def build_mediapipe_skeleton(mediapipe_pose_data, segment_dataframe, mediapipe_landmarks: list[str]) -> list:
    num_frames = mediapipe_pose_data[0]
    num_frames_range = range(num_frames)

    mediapipe_frame_segment_joint_XYZ = []

    for frame in track(num_frames_range, description="Building Mediapipe Skeleton"):
        trunk_joint_connection = [
            "left_shoulder",
            "right_shoulder",
            "left_hip",
            "right_hip",
        ]
        trunk_virtual_markers = build_virtual_trunk_marker(mediapipe_pose_data, mediapipe_landmarks, trunk_joint_connection, frame)

        mediapipe_skeleton_coordinates = []
        for (segment, segment_info) in segment_dataframe.iterrows():
            if segment == "trunk":
                mediapipe_skeleton_coordinates[segment] = [trunk_virtual_markers[0], trunk_virtual_markers[1]]
            
            elif segment == "left_hand" or segment == "right_hand":
                proximal_joint_hand = segment_info["Joint_Connection"][0]
                if segment == "left_hand":
                    distal_joint_hand = "left_index"
                else:
                    distal_joint_hand = "right_index"

                proximal_joint_hand_index = mediapipe_landmarks.index(proximal_joint_hand)
                distal_joint_hand_index = mediapipe_landmarks.index(distal_joint_hand)

                mediapipe_skeleton_coordinates[segment] = [
                    mediapipe_pose_data[frame, proximal_joint_hand_index, :],
                    mediapipe_pose_data[frame, distal_joint_hand_index, :]
                ]
            
            elif segment == "left_foot" or segment == "right_foot":
                if segment == "left_foot":
                    proximal_joint_foot_name = "left_ankle"
                else:
                    proximal_joint_foot_name = "right_ankle"

                proximal_joint_foot_index =  mediapipe_landmarks.index(proximal_joint_foot_name)

                distal_joint_foot = segment_info["Joint_Connection"][1]
                distal_joint_foot_index = mediapipe_landmarks.index(distal_joint_foot)
                mediapipe_skeleton_coordinates[segment] = [
                    mediapipe_pose_data[frame, proximal_joint_foot_index, :],
                    mediapipe_pose_data[frame, distal_joint_foot_index, :]
                ]

            else:
                proximal_joint_name = segment_info["Joint_Connection"][0]
                distal_joint_name = segment_info["Joint_Connection"][1]

                proximal_joint_index = mediapipe_landmarks.index(proximal_joint_name)
                distal_joint_index = mediapipe_landmarks.index(distal_joint_name)

                mediapipe_skeleton_coordinates[segment] = [
                    mediapipe_pose_data[frame, proximal_joint_index, :],
                    mediapipe_pose_data[frame, distal_joint_index, :]
                ]

        mediapipe_frame_segment_joint_XYZ.append(mediapipe_skeleton_coordinates)

    return mediapipe_frame_segment_joint_XYZ

def build_virtual_trunk_marker(pose_data, landmarks, trunk_joint_connection, frame):
    trunk_marker_indices = get_indices_of_joints(landmarks, trunk_joint_connection)
    trunk_XYZ_coords = get_XYZ_coordinates_of_markers(pose_data, trunk_marker_indices, frame)
    trunk_proximal = (trunk_XYZ_coords[0] + trunk_XYZ_coords[1]) / 2
    trunk_distal = (trunk_XYZ_coords[2] + trunk_XYZ_coords[3]) / 2
    return trunk_proximal, trunk_distal

def get_indices_of_joints(landmarks, joint_names_list):
    indices = []
    for name in joint_names_list:
        index = landmarks.index(name)
        indices.append(index)
    return indices

def get_XYZ_coordinates_of_markers(pose_data, joint_indices_list, frame):
    XYZ_coords = []
    for index in joint_indices_list:
        joint_coord = pose_data[frame, index, :]
        XYZ_coords.append(joint_coord)
    return XYZ_coords

def calculate_segment_COM(body_segment_dataframe: pd.DataFrame, skeleton_coords, num_frame_range) -> list[dict]:
    segment_COM_frame_dict = []
    for frame in track(num_frame_range, description="Calculating Segment Center of Mass"):
        segment_COM_dict = {}
        for segment, segment_info in body_segment_dataframe.iterrows():
            segment_XYZ = skeleton_coords[frame][segment]

            segment_proximal = segment_XYZ[0]
            segment_distal = segment_XYZ[1]
            segment_COM_length = segment_info["Segment_COM_Length"]
            segment_COM = segment_proximal + segment_COM_length * (segment_distal - segment_proximal)
            segment_COM_dict[segment] = segment_COM
        segment_COM_frame_dict.append(segment_COM_dict)
    return segment_COM_frame_dict

def reformat_segment_COM(segment_COM_frame_dict: list[dict], num_frame_range: range, num_segments: int) -> np.ndarray:
    segment_COM_frame_imgPoint_XYZ = np.empty([int(len(num_frame_range)), int(num_segments), 3])
    for frame in num_frame_range:
        frame_skeleton = segment_COM_frame_dict[frame]
        for joint_count, segment in enumerate(frame_skeleton.keys()):
            segment_COM_frame_imgPoint_XYZ[frame, joint_count, :] = frame_skeleton[segment]
    return segment_COM_frame_imgPoint_XYZ

def calculate_total_body_COM(body_segment_dataframe: pd.DataFrame, segment_COM_frame_dict: list[dict], num_frames_range: range):
    total_body_COM_frame_XYZ = np.empty([int(len(num_frames_range)), 3])
    for frame in track(num_frames_range, description="Calculating Total Body Center of Mass"):
        frame_total_body_percentages = []
        frame_skeleton = segment_COM_frame_dict[frame]
        
        for segment, segment_info in body_segment_dataframe.iterrows():
            segment_COM = frame_skeleton[segment]
            segment_COM_percentage = segment_info["Segment_COM_Percentage"]
            
            segment_total_body_percentage = segment_COM * segment_COM_percentage
            frame_total_body_percentages.append(segment_total_body_percentage)
        
        frame_total_body_COM = np.nansum(frame_total_body_percentages, axis = 0)
        total_body_COM_frame_XYZ[frame, :] = frame_total_body_COM
    
    return total_body_COM_frame_XYZ


def calculate_center_of_mass(pose_data: np.ndarray, skeleton_coords: list, body_segment_dataframe: pd.DataFrame):
    num_frames = pose_data.shape[0]
    num_frames_range = range(num_frames)
    num_segments = len(body_segment_dataframe)

    segment_COM_frame_dict = calculate_segment_COM(body_segment_dataframe, skeleton_coords, num_frames_range)
    segment_COM_frame_imgPoint_XYZ = reformat_segment_COM(segment_COM_frame_dict, num_frames_range, num_segments)
    total_body_COM_frame_XYZ = calculate_total_body_COM(body_segment_dataframe, segment_COM_frame_dict, num_frames_range)

    return (
        segment_COM_frame_dict, 
        segment_COM_frame_imgPoint_XYZ,
        total_body_COM_frame_XYZ
    )

def run_center_of_mass_calculations(processed_skel3d_frame_marker_xyz: np.ndarray):
    body_segment_dataframe = build_anthropometric_dataframe()
    if not mediapipe_body_names_match(mediapipe_body_landmark_names):
        raise ValueError("Mediapipe body landmark names do not match landmark names defined here. This code will need updating.")
    
    skelCoords_frame_segment_joint_XYZ = build_mediapipe_skeleton(
        processed_skel3d_frame_marker_xyz,
        body_segment_dataframe,
        mediapipe_body_landmark_names,
    )

    (
        segment_COM_frame_dict,
        segment_COM_frame_imgPoint_XYZ,
        totalBody_COM_frame_XYZ
    ) = calculate_center_of_mass(
        processed_skel3d_frame_marker_xyz,
        skelCoords_frame_segment_joint_XYZ,
        body_segment_dataframe
    )

    return segment_COM_frame_imgPoint_XYZ, totalBody_COM_frame_XYZ
