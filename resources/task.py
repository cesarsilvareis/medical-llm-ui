#########################################
# What medical task will my LLM pursue? #
#########################################

# - Task definition relies on the public target
# | So, there is not two equal tasks
# Prompting aims to align the definition to end user expectations

import json
from collections.abc import MutableMapping
from typing import Iterator
from langchain_core.prompts import PromptTemplate

from resources.utils import print_message

class Property:
    
    def __init__(self, name: str, type: type):
        self._name = name
        self._type = type
        self._value = None

    @property
    def info(self) -> tuple[str, type]:
        return self._name, self._type
    
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
    
    def __str__(self) -> str:
        return f"[{self._name}] {self._value if self.defined() else 'UNDEFINED'} ({self._type})"
    
    def __repr__(self) -> str:
        return json.dumps({
            "name": self._name,
            "value": self._value if self.defined() else "UNDEFINED",
            "type": str(self._type)
        })


class MedicalTask(MutableMapping):
    ID: int = 0

    def __init__(self, name: str, **required_inputs):
        self.id = MedicalTask.ID = MedicalTask.ID + 1
        
        self.name = name
        self.properties: set[Property] = set()

        if required_inputs is not None:
            self.update(**required_inputs)
            print(required_inputs)
        
        print(str(self.properties))

    def properties_names(self):
        return set(map(lambda p: p.info[0], self.properties))
    
    def prompting(self, prompt_file: str) -> str:
        prompt = PromptTemplate.from_file(prompt_file)
        
        # Are there not considered variables asked by the prompt? [ERROR]
        if any(v not in iter(self) for v in prompt.input_variables):
            print_message(
                msg=f"The task is missing the variables: {', '.join(set(prompt.input_variables) - set(self))}",
                type="error", exception=LookupError
            )

        # Which properties will be ignored in my Prompt Engineering process? [WARNING]
        if any(p not in prompt.input_variables for p in iter(self)):
            print_message(
                msg=f"Prompt Engineering will ignore the variables: {', '.join(set(self) - set(prompt.input_variables))}",
                type="warning"
            )

        return prompt.format(**self)

    def _find_propery(self, name: str) -> Property|None:
        return next((p for p in self.properties if p.info[0] == name), None) # why is python using 'next' for sets???

    def __getitem__(self, key):
        if not (prop := self._find_propery(name=key)): 
            print_message(f"Property '{key}' not found for the task {self}", "error", exception=KeyError)
        
        return prop.value
    
    def __setitem__(self, key, value):
        if (prop := self._find_propery(name=key)): 
            prop.set_value(value)
            return

        new_prop = Property(name=key, type=type(value))
        new_prop.set_value(value)
        self.properties.add(new_prop)

    def __delitem__(self, key) -> None:
        if not (prop := next((p for p in self.properties if p.info[0] == key), None)):
            print_message(
                msg=f"Property '{key}' cannot be deleted from the task {self} because it does not exist", 
                type="error", exception=KeyError
            )
        self.properties.remove(prop)

    def __iter__(self) -> Iterator:
        return iter({ p.info[0] : p.value for p in self.properties })
    
    def __len__(self) -> int:
        return len(self.properties)
        
    def __str__(self) -> str:
        return json.dumps({
            "id": self.id,
            "name": self.name,
            **self
        })
