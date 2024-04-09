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
from langchain_core.prompts import PromptTemplate

from resources.domain.task import MedicalTask
from resources.utils import print_message

class MedicalTemplate():

    def __init__(self, template_str: str, task: MedicalTask):
        self._template_str = template_str
        self._task = task # unchanged reference with required variables

    @property
    def name(self) -> str:
        return self._task.name
    
    @property
    def template_str(self) -> str:
        return self._template_str
    
    def _get_prompt_template(self) -> PromptTemplate:
        return PromptTemplate.from_template(self._template_str)

    def _check_prompt_validity(self):
        prompt = self._get_prompt_template()
        missing_variables = set(self._task) - set(prompt.input_variables)
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

    def change_template(self, new_template):
        self._template_str = new_template
        self._check_prompt_validity()

    def build(self) -> str:
        self._check_prompt_validity()

        prompt = self._get_prompt_template()

        # Are there non-considered variables asked by the prompt? [ERROR]
        if any(v not in iter(self._task) for v in prompt.input_variables):
            print_message(
                msg=f"Cannot build prompt as task misses the variables: " + \
                    ", ".join(set(prompt.input_variables) - set(self._task)),
                type="error", exception=LookupError
            )

        return prompt.format(**self._task)

    def __str__(self) -> str:
        return self.template_str

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "content": self._template_str
        }

    def save(self, save_file: Path):
        with save_file.open('w') as fp:
            json.dump(self.to_json(), fp, indent=4, sort_keys=False)

    @classmethod
    def load(cls, task: MedicalTask, saved_file: Path) -> 'MedicalTemplate':
        with saved_file.open('r') as fp:
            json_data: dict = json.load(fp)
        assert all(attr in json_data for attr in ["name", "content"])
        
        assert json_data["name"] == task.name

        dummy = cls(
            template_str=json_data["content"],
            task=task
        )

        return dummy
