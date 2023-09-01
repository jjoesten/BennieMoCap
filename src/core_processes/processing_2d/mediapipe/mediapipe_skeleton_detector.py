import logging
logger = logging.getLogger(__name__)

from tqdm import tqdm
from pathlib import Path
from typing import Optional, Callable, Union, List, Tuple
import mediapipe as mp
import numpy as np
import cv2
import multiprocessing

from src.data_layer.session_models.post_processing_parameter_models import MediapipeParametersModel
from src.core_processes.processing_2d.mediapipe.data_models.mediapipe_dataclasses import Mediapipe2dNumpyArrays
from src.core_processes.processing_2d.mediapipe.data_models.mediapipe_skeleton_names_and_connections import mediapipe_tracked_point_names_dict
from src.utilities.video import get_video_paths

from src.system.paths_and_filenames.folder_and_filenames import (
    ANNOTATED_VIDEOS_FOLDER_NAME,
    MEDIAPIPE_2D_NPY_FILENAME,
    MEDIAPIPE_BODY_WORLD_FILENAME
)

from skellycam.opencv.video_recorder.video_recorder import VideoRecorder


mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_holistic = mp.solutions.holistic

body_drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
hand_drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
face_drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

class MediapipeSkeletonDetector:
    def __init__(
        self,
        parameter_model: Optional[MediapipeParametersModel] = None,
        use_tqdm: bool = True
    ):
        if parameter_model is None:
            parameter_model = MediapipeParametersModel()
        
        self._parameter_model = parameter_model
        self._use_tqdm = use_tqdm
        
        self._mediapipe_tracked_point_names_dict = mediapipe_tracked_point_names_dict

        self.body_names_list = self._mediapipe_tracked_point_names_dict["body"]
        self.right_hand_names_list = self._mediapipe_tracked_point_names_dict["right_hand"]
        self.left_hand_names_list = self._mediapipe_tracked_point_names_dict["left_hand"]
        self.face_names_list = self._mediapipe_tracked_point_names_dict["face"]

        self.number_of_body_tracked_points = len(self.body_names_list)
        self.number_of_right_hand_tracked_points = len(self.right_hand_names_list)
        self.number_of_left_hand_tracked_points = len(self.left_hand_names_list)
        self.number_of_face_tracked_points = mp.solutions.face_mesh.FACEMESH_NUM_LANDMARKS_WITH_IRISES

        self.number_of_tracked_points_total = (
            self.number_of_body_tracked_points
            + self.number_of_left_hand_tracked_points
            + self.number_of_right_hand_tracked_points
            + self.number_of_face_tracked_points
        )



    def process_folder(
        self,
        video_folder_path: Union[str, Path],
        output_data_folder_path: Union[str, Path],
        kill_event: multiprocessing.Event = None,
        use_multiprocessing: bool = False
    ) -> Union[np.ndarray, None]:
        video_folder_path = Path(video_folder_path)
        logger.info(f"Processing videos in: {video_folder_path}")

        tasks = self._create_video_processing_tasks(output_data_folder_path=output_data_folder_path, video_folder_path=video_folder_path)

        if use_multiprocessing:
            with multiprocessing.Pool() as pool:
                mediapipe2d_single_camera_npy_array_list = pool.starmap(self.process_video, tasks)
        else:
            mediapipe2d_single_camera_npy_array_list = []
            for task in tasks:
                if kill_event is not None:
                    if kill_event.is_set():
                        break
                mediapipe2d_single_camera_npy_array_list.append(self.process_video(*task))

        body_world_numCams_numFrames_numTrackedPts_XYZ, data2d_numCams_numFrames_numTrackedPts_XY = self._build_output_numpy_array(mediapipe2d_single_camera_npy_array_list)

        self._save_mediapipe2d_data_to_npy(
            data2d_numCams_numFrames_numTrackedPts_XY=data2d_numCams_numFrames_numTrackedPts_XY,
            body_world_numCams_numFrames_numTrackedPts_XYZ=body_world_numCams_numFrames_numTrackedPts_XYZ,
            output_data_folder_path=Path(output_data_folder_path)
        )
        return data2d_numCams_numFrames_numTrackedPts_XY
    
    def _create_video_processing_tasks(self, output_data_folder_path: Union[str, Path], video_folder_path: Union[str, Path]) -> List[Tuple]:
        video_paths = get_video_paths(video_folder=video_folder_path)
        tasks = [
            (
                video_path,
                output_data_folder_path,
                self._parameter_model,
                self._annotate_image,
                self._mediapipe_results_list_to_npy_arrays,
                self._use_tqdm
            )
            for video_path in video_paths
        ]
        return tasks
    
    def _build_output_numpy_array(mediapipe2d_single_camera_npy_array_list) -> np.ndarray:
        all_cameras_data2d_list = [m2d.all_data2d_nFrames_nTrackedPts_XY for m2d in mediapipe2d_single_camera_npy_array_list]
        all_cameras_pose_world_data_list = [m2d.body_world_frameNumber_trackedPointNumber_XYZ for m2d in mediapipe2d_single_camera_npy_array_list]
        all_cameras_right_hand_world_data_list = [m2d.rightHand_frameNumber_trackedPointNumber_XYZ for m2d in mediapipe2d_single_camera_npy_array_list]
        all_cameras_left_hand_world_data_list = [m2d.leftHand_frameNumber_trackedPointNumber_XYZ for m2d in mediapipe2d_single_camera_npy_array_list]
        all_cameras_face_world_data_list = [m2d.face_frameNumber_trackedPointNumber_XYZ for m2d in mediapipe2d_single_camera_npy_array_list]

        number_cameras = len(all_cameras_data2d_list)
        number_frames = all_cameras_data2d_list[0].shape[0]
        number_tracked_points = all_cameras_data2d_list[0].shape[1]
        number_spatial_dimensions = all_cameras_data2d_list[0].shape[2]
        number_body_points = all_cameras_pose_world_data_list[0].shape[1]

        data2d_numCams_numFrames_numTrackedPts_XY = np.empty(
            (
                number_cameras,
                number_frames,
                number_tracked_points,
                number_spatial_dimensions
            )
        )
        body_world_numCams_numFrames_numTrackedPts_XYZ = np.empty(
            (
                number_cameras,
                number_frames,
                number_tracked_points,
                number_spatial_dimensions
            )
        )

        for cam_num in range(number_cameras):
            data2d_numCams_numFrames_numTrackedPts_XY[cam_num, :, :, :] = all_cameras_data2d_list[cam_num]
            pose_3d = all_cameras_pose_world_data_list[cam_num]
            right_hand_3d = all_cameras_right_hand_world_data_list[cam_num]
            left_hand_3d = all_cameras_left_hand_world_data_list[cam_num]
            face_3d = all_cameras_face_world_data_list[cam_num]

            body_world_numCams_numFrames_numTrackedPts_XYZ[cam_num, :, :, :] = np.concatenate(
                (pose_3d, right_hand_3d, left_hand_3d, face_3d), axis=1
            )

            logger.info(f"The shape of body_world_numCams_numFrames_numTrackedPts_XYZ is {body_world_numCams_numFrames_numTrackedPts_XYZ.shape}")

        return data2d_numCams_numFrames_numTrackedPts_XY
        
    
    def _save_mediapipe2d_data_to_npy(
        self,
        data2d_numCams_numFrames_numTrackedPts_XY: np.ndarray,
        body_world_numCams_numFrames_numTrackedPts_XYZ: np.ndarray,
        output_data_folder_path: Union[str, Path],
    ):
        mediapipe_2dData_save_path = Path(output_data_folder_path) / MEDIAPIPE_2D_NPY_FILENAME
        mediapipe_2dData_save_path.parent.mkdir(exist_ok=True, parents=True)
        logger.info(f"saving mediapipe image npy file: {mediapipe_2dData_save_path}")
        np.save(str(mediapipe_2dData_save_path), data2d_numCams_numFrames_numTrackedPts_XY)

        mediapipe_body_world_save_path = Path(output_data_folder_path) / MEDIAPIPE_BODY_WORLD_FILENAME
        mediapipe_body_world_save_path.parent.mkdir(exist_ok=True, parents=True)
        logger.info(f"Saving mediapipe body world npy xyz: {mediapipe_body_world_save_path}")
        np.save(str(mediapipe_body_world_save_path), body_world_numCams_numFrames_numTrackedPts_XYZ)


    @staticmethod
    def process_video(
        video_file_path: Path,
        output_data_folder_path: Path,
        parameter_model: MediapipeParametersModel,
        annotate_image: Callable,
        mediapipe_results_list_to_npy_arrays: Callable,
        use_tqdm: bool = True
    ):
        logger.info(f"Running mediapipe skeleton detection on video: {str(video_file_path)}")

        holistic_tracker = mp_holistic.Holistic(
            model_complexity=parameter_model.mediapipe_model_complexity,
            min_detection_confidence=parameter_model.min_detection_confidence,
            min_tracking_confidence=parameter_model.min_tracking_confidence,
        )

        cap = cv2.VideoCapture(str(video_file_path))

        video_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        video_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        video_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        mediapipe_results_list = []
        annotated_images_list = []

        success, image = cap.read()
        
        if use_tqdm:
            iterator = tqdm(
                range(video_frame_count),
                desc=f"mediapiping video: {video_file_path.name}",
                total=video_frame_count,
                colour="magenta",
                unit="frames",
                dynamic_ncols=True,
            )
        else:
            iterator = range(video_frame_count)

        # iterate over each frame in video
        for _ in iterator:
            if not success or image is None:
                logger.error(f"Failed to load an image from: {str(video_file_path)}")
                raise Exception
            
            mediapipe_results = holistic_tracker.process(image)

            mediapipe_single_frame_npy_data = mediapipe_results_list_to_npy_arrays(
                [mediapipe_results],
                image_width=image.shape[0],
                image_height=image.shape[1],
            )

            # TODO: should this be parameterized instead of hard coded?
            # TODO: This also doesn't appear to do anything, the final variable isn't used
            confidence_threshold = 0.5

            threshold_mask = mediapipe_single_frame_npy_data.body_frameNumber_trackedPointNumber_confidence < confidence_threshold
            mediapipe_single_frame_npy_data.body_frameNumber_trackedPointNumber_XYZ[threshold_mask, :] = np.nan

            mediapipe_results_list.append(mediapipe_results)
            annotated_images_list.append(annotate_image(image, mediapipe_results))

            success, image = cap.read()

        # aggregate frame data
        try:
            annotated_video_path = output_data_folder_path / ANNOTATED_VIDEOS_FOLDER_NAME
            annotated_video_path.mkdir(exist_ok=True, parents=True)
            annotated_video_name = video_file_path.stem + "_mediapipe.mp4"
            annotated_video_save_path = annotated_video_path / annotated_video_name

            logger.info(f"Saving mediapipe annotated video to: {annotated_video_save_path}")

            video_recorder = VideoRecorder()
            video_recorder.save_image_list_to_disk(
                image_list=annotated_images_list,
                path_to_save_video_file=annotated_video_save_path,
                frames_per_second=video_fps
            )
        except Exception as e:
            logger.error(f"Failed to save annotated video file to disk: {e}")
            raise e
        
        # return the aggregated numpy array for this video
        return mediapipe_results_list_to_npy_arrays(
            mediapipe_results_list=mediapipe_results_list,
            image_width=video_width,
            image_height=video_height
        )





    @staticmethod
    def _annotate_image(image, mediapipe_results):
        mp_drawing.draw_landmarks(
            image=image,
            landmark_list=mediapipe_results.face_landmarks,
            connections=mp_holistic.FACEMESH_CONTOURS,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style(),
        )
        mp_drawing.draw_landmarks(
            image=image,
            landmark_list=mediapipe_results.face_landmarks,
            connections=mp_holistic.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style(),
        )
        mp_drawing.draw_landmarks(
            image=image,
            landmark_list=mediapipe_results.pose_landmarks,
            connections=mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style(),
        )
        mp_drawing.draw_landmarks(
            image=image,
            landmark_list=mediapipe_results.left_hand_landmarks,
            connections=mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing_styles.get_default_hand_connections_style(),
        )

        mp_drawing.draw_landmarks(
            image=image,
            landmark_list=mediapipe_results.right_hand_landmarks,
            connections=mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing_styles.get_default_hand_connections_style(),
        )
        return image
    
    def _mediapipe_results_list_to_npy_arrays(
        self,
        mediapipe_results_list: List,
        image_width: Union[int, float],
        image_height: Union[int, float],
    ) -> Mediapipe2dNumpyArrays:
        number_of_frames = len(mediapipe_results_list)
        number_of_spatial_dimensions = 3  # this will be 2d XY pixel data, with mediapipe's estimate of Z

        body_frameNumber_trackedPointNumber_XYZ = np.zeros(
            (
                number_of_frames,
                self.number_of_body_tracked_points,
                number_of_spatial_dimensions,
            )
        )
        body_frameNumber_trackedPointNumber_XYZ[:] = np.nan

        body_world_frameNumber_trackedPointNumber_XYZ = np.zeros(
            (
                number_of_frames,
                self.number_of_body_tracked_points,
                number_of_spatial_dimensions,
            )
        )
        body_world_frameNumber_trackedPointNumber_XYZ[:] = np.nan

        body_frameNumber_trackedPointNumber_confidence = np.zeros(
            (number_of_frames, self.number_of_body_tracked_points)
        )
        body_frameNumber_trackedPointNumber_confidence[:] = np.nan  # only body markers get a 'confidence' value

        rightHand_frameNumber_trackedPointNumber_XYZ = np.zeros(
            (
                number_of_frames,
                self.number_of_right_hand_tracked_points,
                number_of_spatial_dimensions,
            )
        )
        rightHand_frameNumber_trackedPointNumber_XYZ[:] = np.nan

        leftHand_frameNumber_trackedPointNumber_XYZ = np.zeros(
            (
                number_of_frames,
                self.number_of_left_hand_tracked_points,
                number_of_spatial_dimensions,
            )
        )
        leftHand_frameNumber_trackedPointNumber_XYZ[:] = np.nan

        face_frameNumber_trackedPointNumber_XYZ = np.zeros(
            (
                number_of_frames,
                self.number_of_face_tracked_points,
                number_of_spatial_dimensions,
            )
        )
        face_frameNumber_trackedPointNumber_XYZ[:] = np.nan

        all_body_tracked_points_visible_on_frame_bool_list = []
        all_right_hand_points_visible_on_frame_bool_list = []
        all_left_hand_points_visible_on_frame_bool_list = []
        all_face_points_visible_on_frame_bool_list = []
        all_tracked_points_visible_on_frame_list = []

        for frame_number, frame_results in enumerate(mediapipe_results_list):
            # get the Body data (aka 'pose')
            if frame_results.pose_landmarks is not None:
                for landmark_number, landmark_data in enumerate(frame_results.pose_landmarks.landmark):
                    body_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 0] = (
                        landmark_data.x * image_width
                    )
                    body_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 1] = (
                        landmark_data.y * image_height
                    )
                    body_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 2] = (
                        landmark_data.z
                        * image_width
                        # z is on roughly the same scale as x, according to mediapipe docs
                    )
                    body_frameNumber_trackedPointNumber_confidence[
                        frame_number, landmark_number
                    ] = landmark_data.visibility  # mediapipe calls their 'confidence' score 'visibility'

                for landmark_number, landmark_data in enumerate(frame_results.pose_world_landmarks.landmark):
                    body_world_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 0] = (
                        landmark_data.x * image_width
                    )
                    body_world_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 1] = (
                        landmark_data.y * image_height
                    )
                    body_world_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 2] = (
                        landmark_data.z * image_width
                    )

            # get Right Hand data
            if frame_results.right_hand_landmarks is not None:
                for landmark_number, landmark_data in enumerate(frame_results.right_hand_landmarks.landmark):
                    rightHand_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 0] = (
                        landmark_data.x * image_width
                    )
                    rightHand_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 1] = (
                        landmark_data.y * image_height
                    )
                    rightHand_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 2] = (
                        landmark_data.z * image_width
                    )

            # get Left Hand data
            if frame_results.left_hand_landmarks is not None:
                for landmark_number, landmark_data in enumerate(frame_results.left_hand_landmarks.landmark):
                    leftHand_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 0] = (
                        landmark_data.x * image_width
                    )
                    leftHand_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 1] = (
                        landmark_data.y * image_height
                    )
                    leftHand_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 2] = (
                        landmark_data.z * image_width
                    )

            # get Face data
            if frame_results.face_landmarks is not None:
                for landmark_number, landmark_data in enumerate(frame_results.face_landmarks.landmark):
                    face_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 0] = (
                        landmark_data.x * image_width
                    )
                    face_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 1] = (
                        landmark_data.y * image_height
                    )
                    face_frameNumber_trackedPointNumber_XYZ[frame_number, landmark_number, 2] = (
                        landmark_data.z * image_width
                    )

            # check if all tracked points are visible on this frame
            all_body_visible = all(sum(np.isnan(body_frameNumber_trackedPointNumber_XYZ[frame_number, :, :])) == 0)
            all_body_tracked_points_visible_on_frame_bool_list.append(all_body_visible)

            all_right_hand_visible = all(
                sum(np.isnan(rightHand_frameNumber_trackedPointNumber_XYZ[frame_number, :, :])) == 0
            )
            all_right_hand_points_visible_on_frame_bool_list.append(all_right_hand_visible)

            all_left_hand_visible = all(
                sum(np.isnan(leftHand_frameNumber_trackedPointNumber_XYZ[frame_number, :, :])) == 0
            )
            all_left_hand_points_visible_on_frame_bool_list.append(all_left_hand_visible)

            all_face_visible = all(sum(np.isnan(face_frameNumber_trackedPointNumber_XYZ[frame_number, :, :])) == 0)
            all_face_points_visible_on_frame_bool_list.append(all_face_visible)

            all_points_visible = all(
                [
                    all_body_visible,
                    all_right_hand_visible,
                    all_left_hand_visible,
                    all_face_visible,
                ],
            )

            all_tracked_points_visible_on_frame_list.append(all_points_visible)

        return Mediapipe2dNumpyArrays(
            body_frameNumber_trackedPointNumber_XYZ=np.squeeze(body_frameNumber_trackedPointNumber_XYZ),
            body_world_frameNumber_trackedPointNumber_XYZ=np.squeeze(body_world_frameNumber_trackedPointNumber_XYZ),
            rightHand_frameNumber_trackedPointNumber_XYZ=np.squeeze(rightHand_frameNumber_trackedPointNumber_XYZ),
            leftHand_frameNumber_trackedPointNumber_XYZ=np.squeeze(leftHand_frameNumber_trackedPointNumber_XYZ),
            face_frameNumber_trackedPointNumber_XYZ=np.squeeze(face_frameNumber_trackedPointNumber_XYZ),
            body_frameNumber_trackedPointNumber_confidence=np.squeeze(body_frameNumber_trackedPointNumber_confidence),
        )