#!../.venv/bin/python3
import sys
import streamlit as st

from streamlit import runtime
from streamlit.web.cli import main as strunner

from resources import *

@st.cache_resource
def load_participant(target: PublicTarget) -> MedicalEndUser:
    return MedicalEndUser(
        type=target,
        tasks=Loader().load_tasks_from_fs(target=target)
    )

def load_template(target: PublicTarget, task: MedicalTask) -> MedicalTemplate:
    return Loader().load_task_prompt_from_fs(target, task)


def configuration_form(task: MedicalTask):
    properties = sorted(task.keys())

    for prop in properties:
        task[prop] = draw_user_input_for_type(
            value_type=task.prop_type(prop),
            label=from_canonical_prop(prop),
            value=task.prop_value(prop)
        )


def draw_template(target: PublicTarget, task: MedicalTask):
    if "template" not in st.session_state:
        st.session_state["template"] = ""

    if st.button("Submit"):
        st.session_state["template"] = load_template(target, task).build()

    if not st.session_state["template"]: return

    st.subheader("III. Template Result 📩")
    template_col, info_col = st.columns([8.5, 1.5])
    
    with open("resources/style/template.css", 'r') as t:
        template_col.markdown(f'<style>{t.read()}</style>', unsafe_allow_html=True)
    
    template_col.markdown(f'<div class="custom-box">{st.session_state["template"]}</div>', unsafe_allow_html=True)

    with info_col:
        text_copy_button(st.session_state["template"])        
    
    st.image("resources/storage/img/chatgptlogo.png", width=45)
    st.info("Please copy it! And move to **[ChatGPT](%s)** to prompt it!" %("https://chat.openai.com"))

def streamlit_app():

    st.set_page_config(
        page_title="DrGPT - Medical Template",
        page_icon="📓",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    st.title("Encapsulating the Prompt Engineering for Medical Users")

    st.subheader("I. What would you like to ChatGPT do? 👨🏻‍⚕️")

    target_profile = st.selectbox(
        label="👤 Select your public target", 
        options=list(PublicTarget)
    )

    participant = load_participant(target_profile)

    task_name = st.selectbox(
        label=f"📝 What it the task focussing {target_profile}s?", 
        options=participant.tasks_names
    )

    if not task_name: return

    st.divider()

    st.subheader("II. Fill Up the Template ✍🏻")

    task = participant.get_task(name=task_name)
    
    configuration_form(task)

    draw_template(target_profile, task)
    

    with st.sidebar:
        st.json(task.to_json())
             

def main():
    if runtime.exists():
        streamlit_app()
        sys.exit(0)
    
    sys.argv = ["streamlit", "run", sys.argv[0]]
    sys.exit(strunner())


if __name__ == "__main__":
    main()