from typing import List, Dict, Tuple, Optional, Any
from pydantic import BaseModel, Field, root_validator

from src.core_processes.processing_2d.mediapipe.data_models.mediapipe_skeleton_names_and_connections import mediapipe_skeleton_schema

class InfoDict(BaseModel):
    """
    Dictionary of skeleton information about this session.
    segment_lengths
    schemas: schemas used to interpret tracked points (how to connect the tracked points of the skeleton)
    """
    segment_lengths: Dict[str, Any] = Field(default_factory=dict, description="Body segment lengths")
    schemas: List[BaseModel] = Field(default_factory=list, description="Tracked point schemas")

class Point(BaseModel):
    x: Optional[float] = Field(None, description="X-coordinate")
    y: Optional[float] = Field(None, description="Y-coordinate")
    z: Optional[float] = Field(None, description="Z-coordinate")

class Timestamps(BaseModel):
    mean: Optional[float] = Field(None, description="The mean timestamp for this frame")
    by_camera: Dict[str, Any] = Field(default_factory=dict, description="Timestamps for each camera on this frame (key = video name)")

class VirtualMarkerDefinition(BaseModel):
    """A virtual marker, defined by combining multiple markers with weights to generate a new marker point"""
    marker_names: List[str] = Field(default_factory=list, description="Names of the markers that define this virtual marker")
    marker_weights: List[float] = Field(default_factory=list, description="Weights of the markers that define this virtual marker, must sum to 1")

    @root_validator(skip_on_failure=True)
    def check_weights(cls, values):
        marker_weights = values.get("marker_weights")
        if sum(marker_weights) != 1:
            raise ValueError(f"Marker weights must sum to 1, actual {marker_weights}")
        return values

class SegmentSchema(BaseModel):
    """Schema for a segment of a skeleton, defined by a set of traced points and the connection between them."""
    point_names: List[str] = Field(default_factory=list, description="Names of the tracked points that define this segment")
    virtual_marker_definitions: Optional[Dict[str, VirtualMarkerDefinition]] = Field(default_factory=dict, description="Virtual markers that define this segment")
    connections: List[Tuple[int, int]] = Field(default_factory=list, description="Connections between the tracked points")
    parent: Optional[str] = Field(None, description="Name of the parent of this segment")

class SkeletonSchema(BaseModel):
    body: SegmentSchema = Field(default_factory=SegmentSchema, description="Tracked points that define the body")
    hands: Dict[str, SegmentSchema] = Field(default_factory=dict, description="Tracked points that define the hands: keys - (left, right)")
    face: SegmentSchema = Field(default_factory=SegmentSchema, description="Tracked points that define the face")

    def __init__(self, schema_dict: Dict[str, Any]):
        super().__init__()
        self.body = SegmentSchema(**schema_dict["body"])
        self.hands = {hand: SegmentSchema(**hand_schema) for hand, hand_schema in schema_dict["hands"].items()}
        self.face = SegmentSchema(**schema_dict["face"])

    def to_dict(self):
        d = {}
        d["body"] = self.body.model_dump()
        d["hands"] = {hand: hand_schema.model_dump() for hand, hand_schema in self.hands.items()}
        d["face"] = self.face.model_dump()
        return d

class FrameData(BaseModel):
    """Data for a single frame"""
    timestamps: Timestamps = Field(default_factory=Timestamps, description="Timestamp data")
    tracked_points: Dict[str, Point] = Field(default_factory=dict, description="The points being tracked")

    @property
    def tracked_point_names(self):
        return list(self.tracked_points.keys())
    
    @property
    def timestamp(self):
        return self.timestamps.mean
    
    def to_dict(self) -> dict:
        d = {}
        d["timestamps"] = self.timestamps.model_dump()
        d["tracked_points"] = {name: point.model_dump() for name, point in self.tracked_points.items()}
        return d