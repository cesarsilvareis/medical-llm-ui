#################################################
# What public demographics will my LLM look to? #
#################################################

# - End User can differ from Active User, which is a medical participant
# | But, all medical users (included Patients) can be Active Users.
# - Prompting guided to well-defined task
# | As such, the task exclusively attends to a particular public target (no overlap allowed)

from resources.utils import ExtendedEnum
from resources.task import MedicalTask

class Target(ExtendedEnum):
    PATIENT             = 0
    NON_MEDICAL_STUDENT = 1
    MEDICAL_STUDENT     = 2
    PHYSICIAN           = 3


class MedicalEndUser():

    def __init__(self, type: Target, tasks: list[MedicalTask]):
        self._type = type
        self._tasks = tasks

    @property
    def type(self) -> Target:
        return self._type

    @property
    def tasks(self) -> list[MedicalTask]:
        return self._tasks.copy()
