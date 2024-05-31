#!../.venv/bin/python3
import sys
import streamlit as st

from streamlit import runtime
from streamlit.web.cli import main as strunner
from streamlit.delta_generator import DeltaGenerator

from resources import *

@st.cache_resource
def load_participant(target: PublicTarget) -> MedicalEndUser:
    return MedicalEndUser(
        type=target,
        tasks=Loader().load_tasks_from_fs(target=target)
    )

def load_template(target: PublicTarget, task: MedicalTask) -> MedicalTemplate:
    return Loader().load_task_prompt_from_fs(target, task)


def configuration_form(task: MedicalTask) -> bool:
    def draw_input_properties(column: DeltaGenerator, properties: list[str]):
        with column:
            for prop in properties:
                task[prop] = draw_user_input_for_type(
                    value_type=task.prop_type(prop),
                    label=from_canonical_prop(prop),
                    value=task.prop_value(prop, default=True)
                )

    properties = sorted(task.keys())
    c1, c2 = st.columns(2)
    draw_input_properties(c1, properties[::2])
    draw_input_properties(c2, properties[1::2])

    c1, c2 = st.columns([2, 8])
    if c1.button("Submit"):
        c2.success("Check the result below!")
        return True
    return False


def draw_template(submitted: bool, target: PublicTarget, task: MedicalTask):
    template_id = lambda: hash(target) + hash(task)

    if "template" not in st.session_state or template_id() != st.session_state.get("template_id", 0):
        st.session_state["template"] = ""

    if submitted and (template := load_template(target, task)) is not None:
        st.session_state["template"] = template.build()
        st.session_state["template_id"] = template_id()

    if not st.session_state["template"]: return

    st.subheader("III. Template Result 📩")

    template_col, info_col = st.columns([9.5, .5])
    
    template_col.markdown(
        link_ref_to_html("resources/static/style/template.css", "css"),
        unsafe_allow_html=True
    )
    
    template_col.markdown(f'<div class="custom-box">\n\n{st.session_state["template"]}</div>', unsafe_allow_html=True)

    with info_col:
        text_copy_button(st.session_state["template"])        
    
    st.image("resources/storage/img/chatgptlogo.png", width=45)
    st.info("Please copy the template! 👉 Move to **[ChatGPT](%s)** to prompt it!" \
            %("https://chat.openai.com"))

def streamlit_app():

    st.set_page_config(
        page_title="DrGPT - Medical Template",
        page_icon="📓",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    st.title("Encapsulating the Prompt Engineering for Medical Users")

    st.subheader("I. What would you like **ChatGPT** to do for you? 👨🏻‍⚕️")

    target_profile = st.selectbox(
        label="👤 Select your public target", 
        options=list(PublicTarget)
    )

    participant = load_participant(target_profile)

    task_name = st.selectbox(
        label=f"📝 Idealize a task tailored to **{target_profile}s**", 
        options=participant.tasks_names
    )

    if not task_name: return

    st.divider()

    st.subheader("II. Fill Up the Template ✍🏻")

    task = participant.get_task(name=task_name)
    
    form_submitted = configuration_form(task)
    st.divider()
    draw_template(form_submitted, target_profile, task)
    

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