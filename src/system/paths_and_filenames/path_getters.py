from pathlib import Path

from src.system.paths_and_filenames.folder_and_filenames import (
    BASE_DATA_FOLDER_NAME
)



def home_dir() -> Path:
    return Path.home()

data_folder_path: Path = None
def get_data_folder_path(create_folder: bool = True) -> Path:
    global data_folder_path
    if data_folder_path is None:
        data_folder_path = Path(home_dir(), BASE_DATA_FOLDER_NAME)
        if create_folder:
            data_folder_path.mkdir(exist_ok=create_folder, parents=True)

    return data_folder_path