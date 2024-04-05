#!../.venv/bin/python3
import sys
import streamlit as st

from streamlit import runtime
from streamlit.web.cli import main as strunner

from resources import *

import streamlit as st

@st.cache_resource
def load_participant(target: PublicTarget) -> MedicalEndUser:
    return MedicalEndUser(
        type=target,
        tasks=Loader().load_from_fs(target=target)
    )

def submit_text_and_clear(key, **args) -> str:
    if "text" not in st.session_state:
        st.session_state["text"] = ""

    def submit():
        st.session_state["text"] = st.session_state.get(key)
        st.session_state[key] = ""

    st.text_input(key=key, on_change=submit, **args)     
    result = st.session_state["text"]
    st.session_state["text"] = ""
    return result



def task_creator_form(target: MedicalEndUser) -> MedicalTask:
    with st.expander("Create a new task", expanded=False):
        name = st.text_input(label="Task Name", value="", key="task_name")

        valid_name = False

        if not name or name.replace(" ", "") == "":
            st.warning(f"Please, name your **{target.type}**  task to pursue.")
        elif any(t.name == name for t in target.tasks):
            st.error(f"Invalid name for a task as it already exists for **{target.type}s**")
        else:
            st.success("The task can be added. Select it!")
            valid_name = True

        if not st.button("Submit") or not valid_name:
            print("not added yet")
            return None

        print("added")
        task = MedicalTask(name)
        target.assign(task)
        return task


def parameter_form(task: MedicalTask) -> bool:

    st.subheader(f"Parameter {len(task)}")

    name_col, type_col = st.columns(2)

    with name_col: # declaration
        parameter_name = st.text_input("Parameter Name")

    with type_col:
        parameter_type = st.selectbox("Parameter Type", ["Text", "Number", "Dropdown"])
        if parameter_type == "Text":
            parameter_value = st.text_input("Enter Text Value")
        elif parameter_type == "Number":
            parameter_value = st.number_input("Enter Numeric Value")
        elif parameter_type == "Dropdown":
            options = st.text_input("Enter Dropdown Options (comma-separated)")
            options_list = [option.strip() for option in options.split(",")]
            parameter_value = st.selectbox("Select Dropdown Option", options_list)

    if st.button("Add Parameter"):
        task[parameter_name] = parameter_value
        return True

    return False


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

    task = st.selectbox(
        label="Choose a task to configure in your manner.",
        options=participant.tasks,
        key="selected_task"
    )

    if task_creator_form(participant) is not None:
        st.rerun() # Move to selection

    if task is not None:
        st.header(f"Task *{task}*")
        st.write(task.to_json())
        parameter_form(task)


def main():
    if runtime.exists():
        streamlit_app()
        sys.exit(0)
    
    sys.argv = ["streamlit", "run", sys.argv[0]]
    sys.exit(strunner())


if __name__ == "__main__":
    main()