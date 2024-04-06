################################
# Load Instances from local FS #
################################

import re
from typing import Literal, Union
from pathlib import Path
from resources.domain.target import PublicTarget
from resources.domain.task import MedicalTask

from resources.utils import Singleton, related_to_project_path, print_message

class Loader(metaclass=Singleton):
    TEMPLATE_DIR_PATH = related_to_project_path(__file__, "prompts")
    TASK_DIR_PATH = related_to_project_path(__file__, "tasks")

    def __init__(self):
        self.task_basefiles = { p: Path(f"task-{p}.json") for p in PublicTarget }
        print_message("Loader Access", type="warning")

    def _get_related_file_path(self, file: Path, mode: Literal["task"]) -> Path:
        if mode == "task":
            return self.TASK_DIR_PATH.joinpath(file)
        
    def _file_exists(self, file: Path, mode: Literal["task"]) -> bool:
        return self._get_related_file_path(file, mode).exists()

    def _get_first_file(self, target: PublicTarget, mode: Literal["task"]) -> Path:
        if mode == "task":
            return self.task_basefiles[target]

    def _get_next_file(self, file: Path) -> Path:
        number_match = re.search(r"\d*$", file.stem)
        number = int(number_match.group()) if number_match else 0  
        return Path(f"{file.stem}-{number+1}.json")

    def _get_new_target_file(self, target: PublicTarget, mode: Literal["task"]) -> Path:
        guess = self._get_first_file(target, mode)
        
        while self._file_exists(guess, mode):
            guess = self._get_next_file(guess)            
        
        return guess

    def _get_target_files(self, target: PublicTarget, mode: Literal["task"]) -> list[Path]:
        current_file = self._get_first_file(target, mode)
        target_files = []
        while self._file_exists(current_file, mode):
            target_files.append(current_file)           
            current_file = self._get_next_file(current_file)
        
        return target_files


    def load_to_fs(self, target: PublicTarget, tasks: Union[MedicalTask, set[MedicalTask]]):
        if type(tasks) == MedicalTask:
            tasks = set(tasks)

        for task in tasks:
            task.save(self._get_new_target_file(target, mode="task"))
                

    def load_from_fs(self, target: PublicTarget) -> Union[MedicalTask, set[MedicalTask]]:
        task_files = self._get_target_files(target=target, mode="task")
        load_tasks = { MedicalTask.load(f) for f in task_files }

        return next(iter(load_tasks)) if len(load_tasks) == 1 else load_tasks          
