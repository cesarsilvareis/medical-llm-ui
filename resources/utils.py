import sys
import builtins, datetime
from enum import Enum
from typing import Optional, Literal, Type, Union, Any
from pathlib import Path

#-------------#
# Definitions #
#-------------#

PROJECT_ROOT_PATH = Path(__name__).absolute().parent # running app.py path
DATE_FORMAT = "%d-%m-%Y"

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

def type_to_str(type: Type) -> str:
    return type.__name__

def type_from_str(str: str) -> Type:
    return getattr(
            datetime if str == type_to_str(datetime.date) \
            # ...
            else builtins, 
        str)

def get_typed_value(value: str, type: Type) -> Any:
    if type is datetime.date:
        return datetime.datetime.strptime(value, "%d-%m-%Y").date()
    return type(value)

def print_message(msg: str, type: Literal["error", "warning", "hint"], exception: Optional[Exception]=None):
    print_str = f"[{type.upper()}] {msg}"
    
    if exception is not None:
        raise exception(print_str)
    
    print(print_str, file=sys.stderr)


def related_to_project_path(path: Union[str,Path], suffixes: Optional[Union[str, Path, list[Path]]]=None) -> Path:
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

def user_input_for_type(value_type: Type, **args):
    import streamlit as st

    type_config = {
        int: (st.number_input, { 
            "label": "Enter Integer Value",
            "step": 1
        }),
        float: (st.number_input, {
            "label": "Enter Numeric Value"
        }),
        str: (st.text_input, {
            "label": "Enter the Text"
        }),
        datetime.date: (st.date_input, { 
            "label": "Enter the Date", 
            "format": "DD-MM-YYYY"
        })
    }

    value_config = type_config.get(value_type, None)
    assert value_config

    return value_config[0](**value_config[1], **args)


