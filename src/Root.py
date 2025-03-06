import streamlit as st
st.set_page_config(page_title="Snowflake Prospecting Tool", page_icon="🔍", layout="wide")

from functions.helper_global import *
init_session_state()

if not st.session_state.logged_in:
    pages = {
        "Navigation Pages": [
            st.Page("files/Login.py", title="Login"),
            st.Page("files/Register.py", title="Register"),
        ]
    }
elif st.session_state.logged_in and st.session_state["username"] == 'admin':
    pages = {
        "Navigation Pages": [
            st.Page("files/Home.py", title="Home"),
            st.Page("files/Prospect_Finder.py", title="Prospect Finder"),
            st.Page("files/Message_Generation.py", title="Message Generation"),
            st.Page("files/Chat_History.py", title="Chat History"),
            st.Page("files/Template_Manager.py", title="Template Manager"),
            st.Page("files/Customer_Stories.py", title="Customer Story Manager"),
            st.Page("files/Battle_Cards.py", title="Battle Cards Manager"),
        ]
    }
elif st.session_state.logged_in and st.session_state["username"] != 'guest':
    pages = {
        "Navigation Pages": [
            st.Page("files/Home.py", title="Home"),
            st.Page("files/Prospect_Finder.py", title="Prospect Finder"),
            st.Page("files/Message_Generation.py", title="Message Generation"),
            st.Page("files/Chat_History.py", title="Chat History"),
            st.Page("files/Template_Manager.py", title="Template Manager"),
        ]
    }

else:
    pages = {
    "Navigation Pages": [
        st.Page("files/Home.py", title="Home"),
        st.Page("files/Prospect_Finder.py", title="Prospect Finder"),
        st.Page("files/Message_Generation.py", title="Message Generation"),
    ]
    }
pg = st.navigation(pages)
pg.run()
