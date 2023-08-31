from dataclasses import dataclass
from typing import Dict
import cv2

@dataclass
class CharucoBoardDefinition:
    aruco_marker_dict: Dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)

    # TODO: make this manageable by the interface?
    squares_width: int = 7
    squares_height: int = 5
    black_square_side_length: int = 1
    aruco_marker_length_proportional: float = 0.8

    def __post_init__(self):
        self.charuco_board = cv2.aruco.CharucoBoard(
            size=[self.squares_width, self.squares_height],
            squareLength=self.black_square_side_length,
            markerLength=self.aruco_marker_length_proportional,
            dictionary=self.aruco_marker_dict,
        )

        self.number_charuco_corners = (self.squares_width - 1) * (self.squares_height - 1)