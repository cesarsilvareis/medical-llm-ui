#!../.venv/bin/python3
import sys
import streamlit as st

from streamlit import runtime
from streamlit.web.cli import main as strunner


def streamlit_app():

    st.set_page_config(
        page_title="DrGPT - Medical Template",
        page_icon="📓",
        layout="wide",
    )

    st.write("""
    # Encapsulating the Prompt Engineering for Medical Users #
    """)



def main():
    if runtime.exists():
        streamlit_app()
        sys.exit(0)
    
    sys.argv = ["streamlit", "run", sys.argv[0]]
    sys.exit(strunner())


if __name__ == "__main__":
    main()