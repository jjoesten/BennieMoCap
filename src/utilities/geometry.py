import numpy as np

def rotate_90_degrees_around_x_axis(raw_skel3d: np.ndarray) -> np.ndarray:
    if len(raw_skel3d.shape) != 3:
        raise ValueError("raw skeleton data must have shape (N, M, 3)")
    
    swapped_skel3d = np.zeros(raw_skel3d.shape)
    swapped_skel3d[:, :, 0] = raw_skel3d[:, :, 0]
    swapped_skel3d[:, :, 1] = raw_skel3d[:, :, 2]
    swapped_skel3d[:, :, 2] = raw_skel3d[:, :, 1]

    return swapped_skel3d

def project_3d_data_to_z_plane(skel3d: np.ndarray) -> np.ndarray:
    if len(skel3d.shape) != 3:
        raise ValueError("skeleton data must have shape (N, M, 3)")
    
    projected_skel3d = np.zeros(skel3d.shape)
    projected_skel3d[:, :, 0] = skel3d[:, :, 0]
    projected_skel3d[:, :, 1] = skel3d[:, :, 1]
    projected_skel3d[:, :, 2] = 0

    return projected_skel3d