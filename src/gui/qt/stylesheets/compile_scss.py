from pathlib import Path
from typing import Union
import sass

def compile_scss(scss_path: Union[str, Path], css_path: Union[str, Path]):
    with open(scss_path) as file:
        scss = file.read()

    compiled_css = sass.compile(string=scss)

    with open(css_path, "w") as file:
        file.write(compiled_css)