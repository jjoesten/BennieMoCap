import json
from pydantic import BaseModel

from src.system.paths_and_filenames.path_getters import get_gui_state_json_path

class GuiState(BaseModel):
    charuco_square_size: float = 39

def save_gui_state(gui_state: GuiState):
    with open(str(get_gui_state_json_path), "w") as file:
        json.dump(gui_state.model_dump_json(), file, indent=4)

def load_gui_state() -> GuiState:
    with open(str(get_gui_state_json_path), "r") as file:
        gui_state = GuiState(**json.load(file))
    return gui_state