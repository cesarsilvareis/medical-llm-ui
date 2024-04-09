#!../.venv/bin/python3
import sys
import streamlit as st

from streamlit import runtime
from streamlit.web.cli import main as strunner

from resources import *

@st.cache_data
def load_participant(target: PublicTarget) -> MedicalEndUser:
    return MedicalEndUser(
        type=target,
        tasks=Loader().load_tasks_from_fs(target=target)
    )

def streamlit_app():

    st.set_page_config(
        page_title="DrGPT - Medical Template",
        page_icon="📓",
        layout="wide",
        initial_sidebar_state="auto"
    )

    st.title("Encapsulating the Prompt Engineering for Medical Users")

    result = None

    with st.sidebar:
        st.write("Configuration:")

        target_profile = st.selectbox(
            label="Public Target", 
            options=list(PublicTarget)
        )

        participant = load_participant(target_profile)

        print(participant)

        task_name = st.selectbox(label="Task", options=[
            "IE Guidelines Congress Slide Builder"
        ])

        if not task_name: return

        st.divider()

        task = participant.get_task(name=task_name)
        st.json(task.to_json())

        # theme = st.text_input(label="Theme", value="", max_chars=25)

        # presenter_name = st.text_input(label="Presenter Name", value="", max_chars=15)
        # presenter_affiliation = st.text_input(label="Presenter Affiliation", value="", max_chars=15)
        # date_time = st.date_input("Presentation Date", format="DD/MM/YYYY")

        # objective = st.text_area(label="Objectives", value="Inform possible changes on IE guidelines")
        # audience = st.text_input(label="Targeted Audience", value="Physicians", max_chars=25)

        # tone = st.text_input(label="Tone", value="rigorous", max_chars=20)
        # language = st.selectbox(label="Language", options=["English", "Portuguese"])

        # duration = st.number_input(label="Duration (in minutes)")
        # slide_time = st.number_input(label="Expected Slide Time (slides/min)", value=1)

        if st.button(label="Submit"):
            ...

    # Prompt Placement

    if result is None:
        st.info("No specific configuration has been established for crafting a new prompt.")
        return

    st.write(f"""
    ## Task : {task_name}
    """)
    st.write(result)
    st.info("Please copy it! And move to [ChatGPT](%s) to prompt it!" %("https://chat.openai.com"))
             

def main():
    if runtime.exists():
        streamlit_app()
        sys.exit(0)
    
    sys.argv = ["streamlit", "run", sys.argv[0]]
    sys.exit(strunner())


if __name__ == "__main__":
    main()