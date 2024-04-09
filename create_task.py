#!../.venv/bin/python3
import sys, string, datetime
import streamlit as st

from streamlit import runtime
from streamlit.web.cli import main as strunner

from resources import *


TASK_FORM_KEY = "task_form_expander"
PROPERTY_FORM_KEY = "property_form_expander"

@st.cache_resource
def load_participant(target: PublicTarget) -> MedicalEndUser:
    return MedicalEndUser(
        type=target,
        tasks=Loader().load_tasks_from_fs(target=target)
    )

def create_form(creator, key, button_name, **args):
    # The expand behavior was adapted from the st issue:
    #   - https://discuss.streamlit.io/t/closing-current-expander-and-opening-next-by-button-press/36226/13

    st.markdown("""<style>
        [class^=st-emotion-cache-p5msec] {display: none;}
        </style>""", unsafe_allow_html=True)
    
    if st.session_state.get(key) is None:
        st.session_state[key] = False

    if st.button(label=button_name):
        st.session_state[key] = not st.session_state[key]

    with st.expander(label="<Not Need it>", expanded=st.session_state[key]):
        entity = creator(**args)
        if entity is not None and type(entity) != bool or entity: # fields are valid and form was submitted
            st.session_state[key] = False
        return entity


def task_creator_form(target: MedicalEndUser) -> MedicalTask:
    def is_valid_task(name: str|None=None) -> bool:
        if not name or name.replace(" ", "") == "" or \
                len([c for c in name if c in string.ascii_letters]) < 3:
            st.warning(f"Please, name your task with more than **3 alphabetic letters** to pursue.")
            return False
        if any(t.name == name for t in target.tasks):
            st.error(f"Invalid name for a task as it already exists for **{target.type}s**")
            return False
        st.success("The task can be added. Select it!")
        return True

    name = st.text_input(label="Task Name", value="")

    # Tests task name before creating the submit button
    valid = is_valid_task(name) 
    if not st.button("Submit", key="task_submit") or not valid:
        return None

    task = MedicalTask(name)
    target.assign(task)
    return task


def property_creator_form(task: MedicalTask) -> bool:
    def is_valid_property(name: str|None=None) -> bool:
        if not name or name.replace(" ", "") == "":
            st.warning(f"Please, name your property to pursue.")
            return False
        if name in task :
            st.error(f"Invalid name for the property as it already exists")
            return False
        st.success("The property can be added. **Submit** it and **Select** it!")
        return True

    name = st.text_input(label="Property Name", value="")
    valid = is_valid_property(name)

    parameter_type = type_from_str(st.selectbox(
        label="Type (inmutable)", 
        options=map(lambda t: type_to_str(t), [
            int, 
            float, 
            str, 
            datetime.date,
            list
        ])
    ))

    value = user_input_for_type(parameter_type, help="Default Value")

    required = st.checkbox(label="Required?", value=True, help="Is this a task input? (inmutable)")

    if not st.button("Submit", key="property_submit") or not valid:
        return False

    if required:
        task.to_mutable()

    task[name] = value
    task.to_detailed()
    return True


def prompt_viewer(target: PublicTarget, task: MedicalTask):
    prompt = Loader().load_task_prompt_from_fs(target, task)

    prompt_txt = st.text_area(
        label="Template",
        value=str(prompt) if prompt else "",
        height=400
    )

    if not prompt_txt: return

    copy_col, check_col, save_col = st.columns(3)
    with copy_col:
        text_copy_button(prompt_txt)

    with check_col:
        if prompt:
            if st.button("Check"):
                try:
                    prompt.change_template(prompt_txt)
                    st.success("**Valid!**")
                except Exception as e:
                    st.error(f"**Not Valid Yet** {e}")
    
    with save_col: 
        if not st.button("Save Template"):
            return

        try:
            if prompt is None:
                prompt = MedicalTemplate(
                    template_str=prompt_txt,
                    task=task
                )
            else:
                prompt.change_template(prompt_txt)
        except Exception as e:
            st.error(str(e))
            return

        Loader().load_task_prompt_to_fs(target, prompt)
        st.success("Template Saved!")


def streamlit_app():

    st.set_page_config(
        page_title="DrGPT - Medical Template",
        page_icon="📓",
        layout="centered",
        initial_sidebar_state="auto"
    )

    st.title("[CREATING TASKS] Encapsulating the Prompt Engineering for Medical Users")

    target_profile = st.selectbox(
        label="For whom your task is centered?", 
        options=list(PublicTarget)
    )

    participant = load_participant(target_profile)

    task_name = st.selectbox(
        label="Choose a task to configure in your manner.",
        options=participant.tasks_names,
        key="selected_task"
    )

    if create_form(
        creator=task_creator_form, 
        key=TASK_FORM_KEY,
        button_name=f"Add new {target_profile} Task",
        target=participant) is not None:
        
        st.rerun() # Move to task selection

    if task_name is None: return

    task = participant.get_task(task_name)

    st.header(f"Task *{task}*")
    view_col, edit_col = st.columns(2)
    with view_col:
        save_col, delete_col = st.columns(2)
        with save_col:
            if st.button("Save Task"):
                Loader().load_tasks_to_fs(target_profile, task)
                st.success("Saved")
        with delete_col:
            if st.button("Delete"):
                try:
                    Loader().exclude_task(target_profile, task)
                except FileNotFoundError:
                    st.error("The task was not saved!")
                    return

                participant.remove_task(task)
                st.rerun()

        st.json(task.to_json(), expanded=True)

    with edit_col:
        # Select the parameter to edit
        prop = st.selectbox(label="Property", options=task.keys())

        if create_form(
            creator=property_creator_form, 
            key=PROPERTY_FORM_KEY,
            button_name=f"Add new Property",
            task=task):

            st.rerun() # Move to task selection

        if prop is None: return

        with st.form("update_prop", clear_on_submit=True):
            st.subheader(f"Update *{prop}*")
            new_value = user_input_for_type(task.prop_type(prop))
            submitted = st.form_submit_button()
            if new_value and submitted:
                task[prop] = new_value

        if st.button("Remove Property"):
            assert prop in task

            del task[prop]
            st.rerun()

        st.json(task.prop_to_json(prop))
    
    prompt_viewer(target_profile, task)


def main():
    if runtime.exists():
        streamlit_app()
        sys.exit(0)
    
    sys.argv = ["streamlit", "run", sys.argv[0]]
    sys.exit(strunner())


if __name__ == "__main__":
    main()