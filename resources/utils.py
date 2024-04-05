import sys
from enum import Enum
from typing import Optional, Literal
from pathlib import Path

#-------------#
# Definitions #
#-------------#

PROJECT_ROOT_PATH = Path(__name__).absolute().parent # running app.py path

#---------#
# Classes #
# --------#

class ExtendedEnum(Enum):

    def __str__(self):
        return self.name.lower().capitalize().replace("_", " ")

    @classmethod
    def count(cls: Enum) -> int:
        return len(cls)

    @classmethod
    def list(cls: Enum) -> list:
        return list(map(lambda c: c.value, cls))


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

#------------------#
# Helper Functions #
# -----------------#

def print_message(msg: str, type: Literal["error", "warning", "hint"], exception: Optional[Exception|None]=None):
    print_str = f"[{type.upper()}] {msg}"
    
    if exception is not None:
        raise exception(print_str)
    
    print(print_str, file=sys.stderr)

def related_to_project_path(path: Optional[str|Path], suffixes: Optional[str|Path|list[Path]|None]=None) -> Path:
    actual_path = path if type(path) == Path else Path(path)
    if suffixes:
        if actual_path.is_file():
            actual_path = actual_path.parent

        if type(suffixes) == str:
            actual_path = actual_path.joinpath(Path(suffixes))
        else:
            for suf in list(suffixes):
                actual_path = actual_path.joinpath(suf) # order preserved

    return actual_path.relative_to(Path(PROJECT_ROOT_PATH))
