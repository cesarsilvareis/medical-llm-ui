#####################################
# The element of Prompt Engineering #
#####################################

# - Besides subjective, the process can achieve reliable results on LLMs
# | Medical Education relies on teaching reliable evidence!
# - Complexity flows out through the process (or, sequence of refining prompts)
# | Not all defined variables are required for a task! Some are details.
# - Task can have multiple prompts assigned to (ones more detailed than others)

import json
from pathlib import Path
from typing import Self
from langchain_core.prompts import PromptTemplate

from resources.domain.task import MedicalTask
from resources.utils import print_message

class MedicalPrompt(str):
    def __new__(cls, content: str, **_):
        return super(MedicalPrompt, cls).__new__(cls, content)

    def __init__(self, _, score: int, name: str, iteration: int):
        self.score = score
        self.name = name
        self.iteration = iteration

    def __repr__(self):
        return f"Prompt(\
                content='{str(self)}', \
                score={self.score}, \
                name='{self.name}', \
                iteration={self.iteration}\
            )"

    def __str__(self):
        return super().__str__()


class MedicalTemplate:

    def __init__(self, 
            prompt: MedicalPrompt, 
            task: MedicalTask, 
            to_validate: bool=True
        ):

        self._prompt = prompt
        
        self._task = task # unchanged reference with required variables
        self._content: str = str(prompt)

        if to_validate:
            self._check_prompt_validity()


    @property
    def id(this) -> str:
        return f"{this.task}/{this.iteration}"
    
    @property
    def name(this) -> str:
        return this._prompt.name
    
    @property
    def iteration(this) -> int:
        return this._prompt.iteration
    
    @property
    def score(this) -> int:
        return this._prompt.score

    @property
    def task(this) -> str:
        return this._task.name
    
    @property
    def content(this) -> str:
        return this._content
    
    def _get_prompt_template(self) -> PromptTemplate:
        return PromptTemplate.from_template(self.content)

    def _check_prompt_validity(self):
        template = self._get_prompt_template()
        missing_variables = set(self._task) - set(template.input_variables)
        required_inputs = self._task.get_required_inputs()
        
        # Is prompt not aligned to the task? [ERROR]
        if any(i in required_inputs for i in missing_variables):
            print_message(
                msg="Wrong prompt-task assign! Template missing required variables: " + \
                    ", ".join(missing_variables.intersection(required_inputs)),
                type="error", exception=LookupError
            )

        # Which properties are ignored in my Prompt Engineering process? [WARNING]
        if any(i not in required_inputs for i in missing_variables):
            print_message(
                msg=f"Prompt Engineering ignores the variables: " + \
                    ", ".join(missing_variables - required_inputs),
                type="warning"
            )

    def change_score(self, new_score: int) -> None:
        self._prompt.score = new_score

    def change_template(self, new_template: str|None=None, to_validate: bool=True) -> None:
        self._content = new_template if new_template else str(self._prompt)
        if to_validate:
            self._check_prompt_validity()

    def build(self) -> str:
        self._check_prompt_validity()

        template = self._get_prompt_template()

        # Are there non-considered variables asked by the prompt? [ERROR]
        if any(v not in iter(self._task) for v in template.input_variables):
            print_message(
                msg=f"Cannot build prompt as task misses the variables: " + \
                    ", ".join(set(template.input_variables) - set(self._task)),
                type="error", exception=LookupError
            )

        return template.format(**self._task)

    def __eq__(self, other: Self) -> bool:
        return self.id == other.id
    
    def __lt__(self, other: Self) -> bool:
        return self.iteration < other.iteration

    def __hash__(self) -> int:
        return hash(str(self))

    def __str__(self) -> str:
        return self.content

    def __repr__(self) -> str:
        return str(self)

    def to_json(self) -> dict:
        return {
            "task": self.task,
            "iteration": self.iteration,
            "name": self.name,
            "score": self.score,
            "prompt": self._prompt,
            "template": self.content
        }

    def save(self, save_file: Path):
        with save_file.open('w') as fp:
            json.dump(self.to_json(), fp, indent=4, sort_keys=False)

    @classmethod
    def load(cls, task: MedicalTask, saved_file: Path) -> 'MedicalTemplate':
        with saved_file.open('r') as fp:
            json_data: dict = json.load(fp)
        assert all(attr in json_data for attr in ["task", "iteration", "name", "score", "prompt"])
        
        assert json_data["task"] == task.name

        dummy = cls(
            prompt=MedicalPrompt(
                json_data["prompt"],
                score=json_data["score"],
                name=json_data["name"],
                iteration=json_data["iteration"],
            ),
            task=task,
            to_validate=False
        )

        dummy.change_template(json_data.get("template", None), to_validate=False)

        return dummy
