#!../.venv/bin/python3
import sys, string, datetime
import streamlit as st

from uuid import uuid4
from streamlit import runtime
from streamlit.web.cli import main as strunner
from streamlit.runtime.uploaded_file_manager import UploadedFile

from resources import *


TASK_FORM_KEY = "task_form_expander"
PROPERTY_FORM_KEY = "property_form_expander"

# Using cache resources to keep object references. cache data will create a copy...

@st.cache_resource
def load_participant(target: PublicTarget) -> MedicalEndUser:
    return MedicalEndUser(
        type=target,
        tasks=Loader.load_tasks_from_fs(target=target)
    )

@st.cache_resource(hash_funcs={MedicalTask: MedicalTask.__hash__})
def load_templates_from_fs(target: PublicTarget, task: MedicalTask) -> MedicalTemplate|set[MedicalTemplate]|None:
    return Loader.load_templates_from_fs(target, task)

@st.cache_resource(hash_funcs={MedicalTask: MedicalTask.__hash__, UploadedFile: lambda f: f.file_id})
def load_templates_from_file(task: MedicalTask, file: UploadedFile) -> MedicalTemplate|set[MedicalTemplate]|None:
    return Loader.load_templates_from_file(task, file)


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

    with st.expander(label="", expanded=st.session_state[key]):
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

    value = create_input_for_type(parameter_type, help="Default Value")

    required = st.checkbox(label="Required?", value=True, help="Is this a task input? (inmutable)")

    if not st.button("Submit", key="property_submit") or not valid:
        return False

    if required:
        task.to_mutable()

    task[canonical_prop(name)] = value
    task.to_detailed()
    return True


def template_viewer(template: Optional[MedicalTemplate]):
    if template is None:
        return
    
    if "template_id" not in st.session_state:
        st.session_state["template_id"] = {}

    if template.id not in st.session_state.get("template_id"):
        st.session_state["template_id"][template.id] = str(template), uuid4().hex

    st.write(f"#### {template.iteration} | {template.name} ####")
    template_col, display_col, tool_col = st.columns((4.35, 4.35, 1.35))

    template_col.write(f"##### 🧬 Template #####")
    template_original, hash = st.session_state["template_id"][template.id]
    template_changed = template_col.text_area(
        label="Template",
        key=f"template_{template.id}_{hash}",
        value=template_original,
        label_visibility="hidden",
        height= 24 * (get_rows(line_size=94, words=text2words(template_original)) + 1)
    )
    display_col.write(f"##### 👁️ Display View #####")

    if not template_changed: return

    tools = tool_col.container(height=150, border=True)
    
    copy_btn, display_tgl = tools.columns((2.75, 7.25))
    
    with copy_btn:
        text_copy_button(template_changed)

    to_display = display_tgl.toggle("Display", key=f"display_{template.id}", value=True)

    score_btn, reset_btn = tools.columns((6, 4))

    score_value = score_btn.number_input("Score (1-5⭐)", key=f"score_{template.id}", value=template.score)
    if score_value != template.score:
        template.change_score(new_score=score_value)
    
    if reset_btn.button("Reset", key=f"reset_{template.id}"):
        template_changed = None
        del st.session_state["template_id"][template.id]
    
    if template_changed != str(template):
        template.change_template(template_changed, to_validate=False)  
        st.rerun()

    if to_display:
        try:
            display_col.code(template.build(), language="markdown", line_numbers=True)
        except Exception as e:
            display_col.error(str(e))
    
    st.divider()


def streamlit_app():

    st.set_page_config(
        page_title="DrGPT - Medical Template",
        page_icon="📓",
        layout="wide",
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
    if task is None: return

    st.header(f"Task *{task}*")
    view_col, edit_col = st.columns(2)
    with view_col:
        save_col, delete_col, _ = st.columns((1.5, 1, 7.5))
        if save_col.button("Save Task", type="primary"):
            Loader.load_tasks_to_fs(target_profile, task)
            st.success("Saved")
        if delete_col.button("Delete", type="secondary"):
            try:
                Loader.exclude_task(target_profile, task)
            except FileNotFoundError:
                st.error("The task was not saved!")
                return

            participant.remove_task(task)
            st.rerun()

        st.json(task.to_json(), expanded=True)

    with edit_col:
        # Select the parameter to edit
        st.subheader("Properties")
        prop = st.selectbox(
            label="Property", 
            options=task.keys(),
            format_func=from_canonical_prop)

        if create_form(
            creator=property_creator_form, 
            key=PROPERTY_FORM_KEY,
            button_name=f"Add new Property",
            task=task):

            st.rerun() # Move to task selection

        if prop:
            prop = canonical_prop(prop)

            with st.form("update_prop", clear_on_submit=True):
                st.subheader("Update")
                st.write(f"*{prop}*")
                new_value = create_input_for_type(task.prop_type(prop))
                required = st.checkbox(label="Required", value=task.is_required_property(prop))
                submitted = st.form_submit_button()
                
                if submitted:
                    if not required:
                        task.to_detailed()
                    
                    task[prop] = new_value if new_value else task[prop]
                    task.to_mutable()
                    st.rerun()

            if st.button("Remove Property"):
                assert prop in task

                del task[prop]
                st.rerun()

            st.json(task.prop_to_json(prop))
    
    #
    #   Templates 
    #

    st.subheader("Templates")
    template_file = st.file_uploader("Upload Template File", key=f"upload_{task.name}")
    if template_file is not None:   # From submitted file
        templates = load_templates_from_file(task, template_file)
        if templates is None:
            load_templates_from_file.clear()
    else:                           # From FS loading
        templates = load_templates_from_fs(target_profile, task)
        if templates is None:
            load_templates_from_fs.clear()
    
    # There is no templates available, so nothing more to do here...
    if templates is None: return
    
    templates = settization(templates)

    save_col, delete_col, _ = st.columns((.5, .5, 9))
    if save_col.button("Save All", type="primary"):
        Loader.load_templates_to_fs(target_profile, templates)

    if delete_col.button("Delete All", type="secondary"):
        Loader.exclude_templates(target_profile, task)
        return

    # Presents template one by one
    for template in sorted(templates):
        template_viewer(template)



def main():
    if runtime.exists():
        streamlit_app()
        sys.exit(0)
    
    sys.argv = ["streamlit", "run", sys.argv[0]]
    sys.exit(strunner())


if __name__ == "__main__":
    main()