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
from typing import Iterator, Optional, Type

from resources.utils import *

class Property:
    
    def __init__(self, name: str, type: Type, required=False):
        self._name = name
        self._type = type
        self._value = None
        self._required = required

    @property
    def info(self) -> tuple[str, Type]:
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
    
    def _value_repr(self) -> Any:
        if not self.defined():
            return "UNDEFINED"
        
        if type(self._value) is datetime.date:
            return self._value.strftime("%d-%m-%Y")

        return self._value

    def to_json(self) -> dict:
        return {
            "name": f"{self:can}",
            "value": self._value_repr(),
            "type": type_to_str(self._type),
            "required": self._required
        }
    
    @classmethod
    def from_json(cls, json_dict: dict) -> 'Property':
        assert all(attr in json_dict for attr in [
            "name", 
            "type",
            "required",
            "value"
        ])

        dummy = cls(
            name=from_canonical_prop(json_dict["name"]),
            type=type_from_str(json_dict["type"]),
            required=json_dict["required"]
        )
        dummy.set_value(get_typed_value(json_dict["value"], dummy.info[1]))
        return dummy

    def __str__(self) -> str:
        return str(self.to_json())

    def __repr__(self) -> str:
        return f"Property: info={', '.join(*self.info)}; value={self.value}"

    def __format__(self, format_spec: str) -> str:
        match format_spec:
            case "can": # canonical form
                return canonical_prop(self._name)
            case _:
                return self._name


class MedicalTask(MutableMapping):

    def __init__(self, name: str, **required_inputs):
        self._name = name # unique for a target

        self._req = False
        self._properties: set[Property] = set()

        if required_inputs is not None:
            self.to_mutable()
            self.update(**required_inputs)
            self.to_detailed()

    @property
    def name(self):
        return self._name

    def _find_property(self, name: str) -> Optional[Property]:
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

    def prop_to_json(self, prop_name: str) -> dict:
        if not (prop := self._find_property(name=prop_name)): 
            print_message(f"Property '{prop_name}' not found for the task {self}", "error", exception=KeyError)
        
        return prop.to_json()
    
    def prop_type(self, prop_name: str) -> Type:
        if not (prop := self._find_property(name=prop_name)): 
            print_message(f"Property '{prop_name}' not found for the task {self}", "error", exception=KeyError)
        
        return prop.info[1]

    def to_json(self) -> dict:
        return {
            "name": self._name,
            "properties": list(map(lambda p: p.to_json(), self._properties))                     
        }

    def save(self, save_file: str):
        with open(f"{save_file}", 'w') as fp:
            json.dump(self.to_json(), fp, indent=4, sort_keys=False)
    
    @classmethod
    def load(cls, saved_file: str) -> 'MedicalTask':
        with open(f"{saved_file}", 'r') as fp:
            json_data: dict = json.load(fp)
        assert all(attr in json_data for attr in ["name", "properties"])
        
        dummy = cls(name=json_data["name"])
        properties = list(Property.from_json(prop_data) for prop_data in json_data["properties"])
        for prop in properties:
            if prop.required:
                dummy.to_mutable()
            dummy[prop.info[0]] = prop.value
            dummy.to_detailed()
            continue

        return dummy
        