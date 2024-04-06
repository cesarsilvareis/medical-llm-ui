#################################################
# What public demographics will my LLM look to? #
#################################################

# - End User can differ from Active User, which is a medical participant
# | But, all medical users (included Patients) can be Active Users.
# - Prompting guided to well-defined task
# | As such, the task exclusively attends to a particular public target (no overlap allowed)

from typing import Optional
from resources.utils import ExtendedEnum, print_message
from resources.domain.task import MedicalTask


class PublicTarget(ExtendedEnum):
    PATIENT             = 0
    NON_MEDICAL_STUDENT = 1
    MEDICAL_STUDENT     = 2
    PHYSICIAN           = 3


class MedicalEndUser():

    def __init__(self, type: PublicTarget, tasks: set[MedicalTask]):
        self._type = type
        self._tasks = { t.name : t for t in tasks }

    @property
    def type(self) -> PublicTarget:
        return self._type

    @property
    def tasks(self) -> list[MedicalTask]:
        return list(self._tasks.values())
    
    @property
    def tasks_names(self) -> list[MedicalTask]:
        return list(self._tasks.keys())
    
    def _contains_task(self, task: MedicalTask) -> bool:
        return task.name in self._tasks

    def get_task(self, name: str) -> Optional[MedicalTask]:
        return self._tasks.get(name, None)
    
    def assign(self, task: MedicalTask):
        if self._contains_task(task):
            print_message(f"Task {task} not assign as it already exists!", type="warning")
            return
        
        self._tasks[task.name] = task 
    
    def __str__(self) -> str:
        task_str = "\n-\t".join(self._tasks)
        return f"[{self._type}]\n{task_str}"
