################################
# Load Instances from local FS #
################################

import re, json, io
from enum import Enum
from typing import Union, Optional, Any
from pathlib import Path
from resources.domain.target import PublicTarget
from resources.domain.task import MedicalTask
from resources.domain.template import MedicalTemplate, MedicalPrompt

from resources.utils import *

class LoadMode(Enum):
    TASK        = 1
    TEMPLATE    = 2

MODE_SOURCE_PATHS: dict[LoadMode, Path] = \
{
    LoadMode.TASK: related_to_project_path(__file__, "tasks"),
    LoadMode.TEMPLATE: related_to_project_path(__file__, "templates")
}

MODE_BASEFILES: dict[LoadMode, dict[PublicTarget, Path]] = {
    LoadMode.TASK : { p: Path(f"task-{p}.json") for p in PublicTarget },
    LoadMode.TEMPLATE: { p: Path(f"prompt-{p}.json") for p in PublicTarget }
}


class Loader:

    # HELPER FUNCTIONS ------------------------------------------------------------------------------------------- #

    def _get_related_file_path(file: Path, mode: LoadMode) -> Path:
        return MODE_SOURCE_PATHS[mode].joinpath(file)
        
    def _file_exists(file: Path, mode: LoadMode) -> bool:
        return Loader._get_related_file_path(file, mode).exists()

    def _get_first_file(target: PublicTarget, mode: LoadMode) -> Path:
        return MODE_BASEFILES[mode][target]

    def _get_next_file(file: Path) -> Path:
        basename = file.stem
        if (number := re.search(r"\d+$", basename)) is None:
            basename += "-0"
            number = 0
        else:
            number = int(number.group())

        return Path(re.sub(r"\d+", rf"{number + 1}", basename) + ".json")

    def _get_new_target_file(target: PublicTarget, mode: LoadMode) -> Path:
        guess = Loader._get_first_file(target, mode)
        
        while Loader._file_exists(guess, mode):
            guess = Loader._get_next_file(guess)            
        
        return guess

    def _get_all_target_files(target: PublicTarget, mode: LoadMode) -> set[Path]:
        current_file = Loader._get_first_file(target, mode)
        target_files = set()
        while Loader._file_exists(current_file, mode):
            target_files.add(current_file)           
            current_file = Loader._get_next_file(current_file)
        
        return target_files
    
    def _get_specified_target_files(target: PublicTarget, mode: LoadMode, **specified_cond: dict[str, Any]) -> Union[Path, set[Path]]:
        current_files = Loader._get_all_target_files(target, mode)
        specified_files = set()
        for file in current_files:
            with Loader._get_related_file_path(file, mode).open() as f:
                data: dict = json.load(f)
                if any(key not in data for key in specified_cond): continue
                
                if all(data[key] == value for key, value in specified_cond.items()):
                    specified_files.add(file)

        return set_optional_return(specified_files)

    # TASKS ------------------------------------------------------------------------------------------------------ #
    
    @staticmethod
    def load_tasks_to_fs(target: PublicTarget, tasks: Union[MedicalTask, set[MedicalTask]]) -> None:
        for task in settization(tasks):
            task_file = Loader._get_specified_target_files(target, name=task.name, mode=LoadMode.TASK)
            if task_file is None:
                task_file = Loader._get_new_target_file(target, mode=LoadMode.TASK)
            task.save(Loader._get_related_file_path(task_file, mode=LoadMode.TASK))

    @staticmethod
    def load_tasks_from_fs(target: PublicTarget) -> Optional[Union[MedicalTask, set[MedicalTask]]]:
        task_files = Loader._get_all_target_files(target=target, mode=LoadMode.TASK)
        load_tasks = { MedicalTask.load(target, Loader._get_related_file_path(f, mode=LoadMode.TASK)) for f in task_files }

        return set_optional_return(load_tasks) 

    @staticmethod
    def exclude_task(target: PublicTarget, task: MedicalTask) -> None:
        if (task_file := Loader._get_specified_target_files(target, name=task.name, mode=LoadMode.TASK)) is None:
            print_message(f"Cannot delete the task '{task.name}' as it lost its source file", "error", FileNotFoundError)
        Loader._get_related_file_path(task_file, mode=LoadMode.TASK).unlink()

    # TEMPLATES -------------------------------------------------------------------------------------------------- #
    
    @staticmethod
    def load_templates_to_fs(target: PublicTarget, templates: Union[MedicalTemplate, set[MedicalTemplate]]) -> None:
        for template in settization(templates):
            template_file = Loader._get_specified_target_files(target, task=template.task, iteration=template.iteration, mode=LoadMode.TEMPLATE)
            if template_file is None:
                template_file = Loader._get_new_target_file(target, mode=LoadMode.TEMPLATE)
            template.save(Loader._get_related_file_path(template_file, mode=LoadMode.TEMPLATE))

    @staticmethod
    def load_templates_from_fs(target: PublicTarget, task: MedicalTask) -> Optional[Union[MedicalTemplate, set[MedicalTemplate]]]:
        if Loader._get_specified_target_files(target, name=task.name, mode=LoadMode.TASK) is None:
            return None
        if (template_files := Loader._get_specified_target_files(target, task=task.name, mode=LoadMode.TEMPLATE)) is None:
            return None

        load_templates = { MedicalTemplate.load(task, Loader._get_related_file_path(f, mode=LoadMode.TEMPLATE)) 
                            for f in settization(template_files) }
        return set_optional_return(load_templates)
    
    @staticmethod
    def load_templates_from_file(task: MedicalTask, file: io.BytesIO) -> Optional[Union[MedicalTemplate, set[MedicalTemplate]]]:
        if file is None: return None

        prompt_pattern = re.compile(r'Prompt (\d+): *(\w+[ \-\w]*)\r?\n(.+?)\r?\n===\r?\n', re.DOTALL)
    
        file_data = file.read().decode("utf-8")
        template_data = prompt_pattern.findall(file_data)
        
        return set_optional_return({ 
                MedicalTemplate(
                    prompt=MedicalPrompt(
                        prompt_content.replace("\r", "").replace("{", "{{").replace("}", "}}"),
                        name=prompt_name,
                        iteration=prompt_id,
                        score=0,
                    ),
                    task=task,
                    to_validate=False,
                ) for prompt_id, prompt_name, prompt_content in template_data
            })
    
    @staticmethod
    def exclude_templates(target: PublicTarget, task: MedicalTask) -> None:
        if Loader._get_specified_target_files(target, name=task.name, mode=LoadMode.TASK) is None:
            print_message(f"Cannot delete templates of a task ('{task.name}') that does not exist", "error", FileNotFoundError)
        
        if (template_files := Loader._get_specified_target_files(target, task=task.name, mode=LoadMode.TEMPLATE)) is None:
            print_message(f"Task ('{task.name}') does not have any template to delete", "error", FileNotFoundError)

        for template_file in settization(template_files):
            Loader._get_related_file_path(template_file, mode=LoadMode.TEMPLATE).unlink()

