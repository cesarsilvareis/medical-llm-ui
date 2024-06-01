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

@st.cache_resource(hash_funcs={MedicalTask: MedicalTask.__hash__})
def load_template(target: PublicTarget, task: MedicalTask) -> MedicalTemplate|None:
    if (task_templates := Loader.load_templates_from_fs(target, task)) is None:
        return None
    
    return max(task_templates, key=lambda t: (t.score, t.iteration)) # (higher) score >> (last) iteration 


def configuration_form(task: MedicalTask, template: MedicalTemplate) -> bool:
    def draw_input_properties(column: DeltaGenerator, properties: list[str]):
        with column:
            for prop in properties:
                if prop not in task:
                    continue

                task[prop] = draw_user_input_for_type(
                    value_type=task.prop_type(prop),
                    label=from_canonical_prop(prop),
                    value=task.prop_value(prop, default=True)
                )

    properties = sorted(template.get_required_variables())
    c1, c2 = st.columns(2)
    draw_input_properties(c1, properties[::2])
    draw_input_properties(c2, properties[1::2])

    c1, c2 = st.columns([2, 8])
    if c1.button("Submit"):
        c2.success("Check the result below!")
        return True
    return False


def draw_template(template: MedicalTemplate|None):
    st.subheader("III. Template Result 📩")
    
    prompt = template.build()

    st.write(f"**Obtained Prompt:** {template.iteration} | {template.name} ({template.score} ⭐ ; *{len(prompt)} characters*)")

    # if "template" not in st.session_state:
    #     st.session_state["template"] = {}
    # if template.id != st.session_state.get("template_id", -1):
    #     st.session_state["template"][template.id] = str(template)

    template_col, copy_col = st.columns([9.5, .5])
    
    template_col.markdown(
        link_ref_to_html("resources/static/style/template.css", "css"),
        unsafe_allow_html=True
    )

    template_col.markdown(f'<div class="custom-box">\n\n{prompt}</div>', unsafe_allow_html=True)

    with copy_col:
        text_copy_button(text=prompt)        
    
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

    st.subheader("II. Fill out the Template ✍🏻")

    task = participant.get_task(name=task_name)
    template = load_template(target_profile, task)
    if template is None:
        st.write("No available templates for this task")

    form_submitted = configuration_form(task, template)
    if form_submitted:
        st.divider()
        draw_template(template)
    

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