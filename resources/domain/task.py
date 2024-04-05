#########################################
# What medical task will my LLM pursue? #
#########################################

# - Task definition relies on the public target
# | So, there is not two equal tasks
# - Each task has UI mutable, required inputs (what really define the task)
# | However, the reached prompt might need more! (e.g., patient profile)
# - Prompting aims to align the task definition to end user expectations

import json
from collections.abc import MutableMapping
from typing import Iterator

from resources.utils import print_message

class Property:
    
    def __init__(self, name: str, type: type, required=False):
        self._name = name
        self._type = type
        self._value = None
        self._required = required

    @property
    def info(self) -> tuple[str, type]:
        return self._name, self._type
    
    @property
    def required(self):
        return self._required
    
    @property
    def value(self):
        return self._value
    
    def defined(self) -> bool:
        return self._value is not None

    def set_value(self, value):
        # if self.defined():
        #     print_message(f"The property {self} already has a value", "error", RuntimeError)
        
        if type(value) != self._type:
            print_message(f"The type of the given value differs from the property type", "error", TypeError)

        self._value = value
    
    def to_json(self):
        return json.dumps({
            "name": self._name,
            "value": str(self._value) if self.defined() else "UNDEFINED",
            "type": str(self._type),
            "required": self._required
        }, indent=4)
    
    @classmethod
    def from_json(cls, json_dict: dict) -> 'Property':
        dummy = cls.__new__(cls)
        for atr, val in json_dict.items():
            setattr(dummy, f"_{atr}", val)
        return dummy

    def __str__(self) -> str:
        return str(self.to_json())

    def __repr__(self) -> str:
        return str(self)


class MedicalTask(MutableMapping):
    ID: int = 0

    def __init__(self, name: str, **required_inputs):
        self._id = MedicalTask.ID = MedicalTask.ID + 1
        
        self._req = False
        self._name = name
        self._properties: set[Property] = set()

        if required_inputs is not None:
            self.to_mutable()
            self.update(**required_inputs)
            self.to_detailed()

    @property
    def name(self):
        return self._name

    def _find_property(self, name: str) -> Property|None:
        return next((p for p in self._properties if p.info[0] == name), None) # why is python using 'next' for sets???

    def _is_required_property(self, name: str) -> bool:
        if not (prop := self._find_property(name=name)): 
            return False
        
        return prop.required

    
    def get_required_inputs(self) -> set[str]:
        return set(p for p in dict(**self) if self._is_required_property(p))

    def to_mutable(self): # required input
        self._req = True

    def to_detailed(self): # additional detail
        self._req = False

    def __getitem__(self, key):
        if not (prop := self._find_property(name=key)): 
            print_message(f"Property '{key}' not found for the task {self}", "error", exception=KeyError)
        
        return prop.value
    
    def __setitem__(self, key, value):
        if (prop := self._find_property(name=key)): 
            prop.set_value(value)
            return

        new_prop = Property(name=key, type=type(value), required=self._req)
        new_prop.set_value(value)
        self._properties.add(new_prop)

    def __delitem__(self, key) -> None:
        if not (prop := self._find_property(name=key), None):
            print_message(
                msg=f"Property '{key}' cannot be deleted from the task {self} because it does not exist", 
                type="error", exception=KeyError
            )
        self._properties.remove(prop)

    def __iter__(self) -> Iterator:
        return iter({ p.info[0] : p.value for p in self._properties })
    
    def __len__(self) -> int:
        return len(self._properties)
    
    def __str__(self) -> str:
        return self._name
    
    def __repr__(self) -> str:
        return str(self)

    def __hash__(self) -> int:
        return hash(self._name) + len(self)

    def to_json(self) -> dict:
        return {
            "id": self._id,
            "name": self._name,
            "properties": list(map(lambda p: json.loads(p.to_json()), self._properties))                     
        }

    def save(self, save_file: str):
        with open(f"resources/load/tasks/{save_file}", 'w') as fp:
            json.dump(self.to_json(), fp, indent=4, sort_keys=False)
    
    @classmethod
    def load(cls, save_file: str) -> 'MedicalTask':
        with open(f"resources/load/tasks/{save_file}", 'r') as fp:
            json_data: dict = json.load(fp)
        dummy = cls.__new__(cls)

        for atr, val in json_data.items():
            if atr == "properties":
                setattr(dummy, "_properties", list(Property.from_json(prop_data) for prop_data in val))
                continue

            setattr(dummy, f"_{atr}", val)

        dummy.to_mutable()
        return dummy
        