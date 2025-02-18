import streamlit as st
###Test
st.set_page_config(page_title="", page_icon="🔍", layout="wide")

pages = {
    "Navigation Pages": [
        st.Page("pages/Home.py", title="Home"),
        st.Page("pages/Prospect_Finder.py", title="Prospect Finder"),
        st.Page("pages/Message_Generation.py", title="Message Generation"),
    ]
}
pg = st.navigation(pages)
pg.run()