import sys, streamlit as st
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

def canonical_prop(prop: str) -> str:
    import re
    return  re.sub(r'[^_\.#a-zA-Z0-9]', '',
            re.sub(r'_+', '_',
            re.sub(r'\(([_\.#a-zA-Z0-9]+)\)', '_in_\g<1>', 
            re.sub(r' ', '_',
            re.sub(r"\.", "_dot_",
            re.sub(r"\-", "_minus_",
            re.sub(r"/", "_per_", prop.lower())))))))

def from_canonical_prop(canonical_prop: str) -> str:
    import re
    return  " ".join(e.capitalize() for e in \
            re.sub(r"_", " ", 
            re.sub(r"in_([\.#/a-zA-Z0-9]+)(_|$)", "(\g<1>)",
            re.sub(r"_dot_", ". ",  
            re.sub(r"_minus_", "-",  
            re.sub(r"_per_", "/", canonical_prop))))).split(" "))

def print_message(msg: str, type: Literal["error", "warning", "hint"], exception: Optional[Exception]=None):
    print_str = f"[{type.upper()}] {msg}"
    
    if exception is not None:
        raise exception(print_str)
    
    print(print_str, file=sys.stderr)

def set_optional_return(my_set: set[Any]) -> Optional[Union[Any, set[Any]]]:
    return my_set if len(my_set) > 1 else next(iter(my_set), None)

def settization(mydata: Any|set[Any]) -> set[Any]:
    return {mydata} if type(mydata) is not set else mydata

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

def text2words(text: str, return_indexes: bool=False) -> list[str]:
    import re
    word_pattern = re.compile(
        r'(-? ?\(?\w+[\.:\-\;),?]?| ?"[\w`]+"\)?|:?[\.\-<"#\*/{}>]{2,}| &|\n)'
    )
    if not return_indexes:
        return word_pattern.findall(text)

    matches = word_pattern.finditer(text)
    return [(match.group(), match.start()) for match in matches]

def get_rows(line_size: int, words: list[str]) -> int:
    if words == list():
        return 0

    remaining_space = line_size # measured in number of chars
    if len(words[0]) > remaining_space:
        raise ValueError(f"Getting Row ERROR: '{words[0]}' does not fit in line.\n") 

    for i, word in enumerate(words):
        if word == "\n":
            return 1 + get_rows(line_size, words[i+1:]) # erase new line char
        if len(word) > remaining_space:
            return 1 + get_rows(line_size, words[i:]) # including itself as it does not fit
        
        # line still not cutted down
        remaining_space -= len(word)

    return 1 # line has not been completed but counts aswell

def create_input_for_type(value_type: Type, **args) -> Any:

    def list_handler(**lst_args):
        num_options = st.number_input(
            label="Number of Options",
            value=0,
            step=1,
            **lst_args
        )
        options = []
        for i in range(num_options):
            option = st.text_input(
                label=f"Option {i + 1}",
                max_chars=25
            )
            if not option:
                continue

            if option in options:
                st.warning("Found repeated options!")
                return []

            options.append(option)
        return options

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
        }),
        list: (list_handler, {})
    }

    value_config = type_config.get(value_type, None)
    assert value_config

    return value_config[0](**value_config[1], **args)

def draw_user_input_for_type(value_type: Type, **args):
    
    def list_handler(value: Optional[list], **args):
        if value is None or not isinstance(value, list):
            value = []
        return st.selectbox(options=value, **args)
    
    type_config = {
        int: (st.number_input, { "step": 1 }),
        float: (st.number_input, {}),
        str: (st.text_input, {}),
        datetime.date: (st.date_input, { "format": "DD-MM-YYYY" }),
        list: (list_handler, {})
    }

    value_config = type_config.get(value_type, None)
    assert value_config

    return value_config[0](**value_config[1], **args)


def link_ref_to_html(ref_file: Union[str, Path], ext: Literal["css", "js"]):
    tag = {
        "css": "style",
        "js": "script"
    }.get(ext)

    if not tag: return

    if type(ref_file) is str:
        ref_file = Path(ref_file)
    
    with ref_file.open('r') as rf:
        return f'<{tag}>{rf.read()}</{tag}>'


def text_copy_button(text: str):
    from streamlit.components.v1 import html

    copy_text = text.replace("`", "\`")
    html(
        f"""
        {link_ref_to_html(ref_file="./resources/static/style/copy_button.css", ext="css")}
        <button id="copy" class="copy-btn">📋</button> 
        {link_ref_to_html(ref_file="./resources/static/js/clipboard_copy.js", ext="js")}
        <script>copyToClipboard(`{copy_text}`)</script>
        """, 
        width=38.5, 
        height=38.5
    )

