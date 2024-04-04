import sys
from enum import Enum
from typing import Optional, Literal

#---------#
# Classes #
# --------#

class ExtendedEnum(Enum):

    def __str__(self):
        return str(self.name)

    @classmethod
    def count(cls: Enum) -> int:
        return len(cls)

    @classmethod
    def list(cls: Enum) -> list:
        return list(map(lambda c: c.value, cls))


#------------------#
# Helper Functions #
# -----------------#

def print_message(msg: str, type: Literal["error", "warning", "hint"], exception: Optional[Exception|None]=None):
    print_str = f"[{type.upper()}] {msg}"
    
    if exception is not None:
        raise exception(print_str)
    
    print(print_str, file=sys.stderr)
