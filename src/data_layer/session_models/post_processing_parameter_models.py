import logging
logger = logging.getLogger(__name__)

from pydantic import BaseModel
from src.data_layer.session_models.session_info_model import SessionInfoModel

class MediapipeParametersModel(BaseModel):
    use_multiprocessing: bool = False
    mediapipe_model_complexity: int = 2
    min_detection_confidence: float = 0.5
    min_tracking_confidence: float = 0.5
    static_image_mode: bool = False
    skip_2d_image_tracking: bool = False

class AniposeTriangulate3DParametersModel(BaseModel):
    confidence_threshold_cutoff: float = 0.5
    use_triangulate_ransac_method: bool = False
    skip_3d_triangulation: bool = False

class ButterworthFilterParametersModel(BaseModel):
    sampling_rate: float = 30
    cutoff_frequency: float = 7
    order: int = 4

class PostProcessingParametersModel(BaseModel):
    framerate: float = 30.0
    butterworth_filter_parameters: ButterworthFilterParametersModel = ButterworthFilterParametersModel()
    max_gap_to_fill: int = 10
    skip_butterworth_filter: bool = False

class PostProcessingParameterModel(BaseModel):
    session_info_model: SessionInfoModel = None
    mediapipe_parameters_model: MediapipeParametersModel = MediapipeParametersModel()
    anipose_triangulate_3d_parameters_model: AniposeTriangulate3DParametersModel = AniposeTriangulate3DParametersModel()
    post_processing_parameters_model: PostProcessingParametersModel = PostProcessingParametersModel()

    class Config:
        arbitrary_types_allowed: bool = True