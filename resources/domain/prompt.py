#####################################
# The element of Prompt Engineering #
#####################################

# - Besides subjective, the process can achieve reliable results on LLMs
# | Medical Education relies on teaching reliable evidence!
# - Complexity flows out through the process (or, sequence of refining prompts)
# | Not all defined variables are required for a task! Some are details.
# - Task can have multiple prompts assigned to (ones more detailed than others)

from pathlib import Path
from langchain_core.prompts import PromptTemplate

from resources.domain.task import MedicalTask
from resources.utils import print_message

class MedicalTemplate():

    def __init__(self, source_file: Path, task: MedicalTask):
        self._task = task # with required variables
        self.prompt = PromptTemplate.from_file(f"resources/load/prompts/{source_file}")

    @property
    def id(self) -> str:
        return self._task._name

    def _check_prompt_validity(self):
        missing_variables = set(self._task) - set(self.prompt.input_variables)
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


    def build(self) -> str:
        
        self._check_prompt_validity()

        # Are there non-considered variables asked by the prompt? [ERROR]
        if any(v not in iter(self._task) for v in self.prompt.input_variables):
            print_message(
                msg=f"Cannot build prompt as task misses the variables: " + \
                    ", ".join(set(self.prompt.input_variables) - set(self._task)),
                type="error", exception=LookupError
            )

        return self.prompt.format(**self._task)
