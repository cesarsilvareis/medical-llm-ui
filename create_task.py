#!../.venv/bin/python3
import sys, string, datetime
import streamlit as st

from streamlit import runtime
from streamlit.web.cli import main as strunner

from resources import *

import streamlit as st

TASK_FORM_KEY = "task_form_expander"
PROPERTY_FORM_KEY = "property_form_expander"

@st.cache_resource
def load_participant(target: PublicTarget) -> MedicalEndUser:
    return MedicalEndUser(
        type=target,
        tasks=Loader().load_from_fs(target=target)
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
        if not name or name.replace(" ", "") == "" or \
                any(c not in string.ascii_letters for c in name) or len(name) < 3:
            st.warning(f"Please, name your property **only using alphabetic letters (+2)** to pursue.")
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
            datetime.date
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
        if st.button("Save Task"):
            Loader().load_to_fs(target_profile, task)
            st.success("Saved")
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

        st.json(task.prop_to_json(prop))


def main():
    if runtime.exists():
        streamlit_app()
        sys.exit(0)
    
    sys.argv = ["streamlit", "run", sys.argv[0]]
    sys.exit(strunner())


if __name__ == "__main__":
    main()