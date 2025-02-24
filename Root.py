import streamlit as st
st.set_page_config(page_title="Snowflake Prospecting Tool", page_icon="🔍", layout="wide")

from functions.helper_global import *
init_session_state()

if not st.session_state.logged_in:
    pages = {
        "Navigation Pages": [
            st.Page("pages/Login.py", title="Login"),
            st.Page("pages/Register.py", title="Register"),
        ]
    }

elif st.session_state.logged_in and st.session_state["username"] != 'guest':
    pages = {
        "Navigation Pages": [
            st.Page("pages/Home.py", title="Home"),
            st.Page("pages/Prospect_Finder.py", title="Prospect Finder"),
            st.Page("pages/Message_Generation.py", title="Message Generation"),
            st.Page("pages/Chat_History.py", title="Chat History"),
            st.Page("pages/Template_Manager.py", title="Template Manager"),
            st.Page("pages/Customer_Stories.py", title="Customer Story Manager"),
            st.Page("pages/Battle_Cards.py", title="Battle Cards Manager"),
        ]
    }

else:
    pages = {
    "Navigation Pages": [
        st.Page("pages/Home.py", title="Home"),
        st.Page("pages/Prospect_Finder.py", title="Prospect Finder"),
        st.Page("pages/Message_Generation.py", title="Message Generation"),
        st.Page("pages/Register.py", title="Account Registration"),
    ]
    }
pg = st.navigation(pages)
pg.run()