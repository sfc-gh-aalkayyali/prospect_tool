import streamlit as st
from functions.helper_global import *

init_session_state()
if st.session_state.username != "guest":
    cols = st.columns([85,15])
    with cols[1]:
        if st.button("Logout", use_container_width=True):
            logout()

st.title(":snowboarder: Home")

st.markdown("---")

col1, col2 = st.columns(2, gap='large')

with col1:
    with st.container(border= False):
        st.subheader(":mag: Prospect Finder")
        st.write(
            "This page allows you to search for prospects, research into their industries, roles, responsibilites, and more all powered by AI.\n\n"
            "Use filters, extract prospect linkedin profile data, query the LLM, send your profiles to Message Generation."
        )
        if st.button("Go to Prospect Finder", key="page1_btn", use_container_width=True, type="primary"):
            st.switch_page("pages/Prospect_Finder.py")

with col2:
    with st.container(border=False):
        st.subheader(":speech_balloon: Message Generation")
        st.write(
            "This page allows you to generate automated outreach emails, meeting notes, linkedin messages, and more all powered by AI. \n\n"
            "Choose profiles, customer success stories, and add your personalized messages."
        )
        if st.button("Go to Message Generation", key="page2_btn", use_container_width=True, type="primary"):
            st.switch_page("pages/Message_Generation.py")

st.write("")
st.write("")

st.subheader("Frequently Asked Questions")
with st.expander(label="How does Prospect Finder Work?"):
    st.write("---")
    st.markdown(
        "We use a **Retrieval Augmented Generation (RAG)** technique to fetch LinkedIn profiles.\n\n"
        "**There are two main components:**\n"
        "1. **Cortex Search**\n"
        "   - Cortex Search performs a vector and keyword “fuzzy” search over stored LinkedIn profiles.\n"
        "   - Default profiles returned: 80 (modifiable in the sidebar under Cortex Search Options).\n\n"
        "2. **Cortex Complete**\n"
        "   - Profiles from Cortex Search are passed into the LLM for refining based on your query.\n"
        "   - Results are displayed in a downloadable tabular format.\n"
        "   - Results in tabular format can be filtered using the sidebar.\n"
    )
    st.markdown("[Learn more about Cortex Search for RAG](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)")
    st.image("https://docs.snowflake.com/en/_images/cortex-search-rag.png", caption="Cortex Search is the retrieval engine that provides the Large Language Model with the context it needs to return answers that are grounded in truth.")

with st.expander(label="How does Message Generation Work?"):
    st.write("---")
    st.markdown(
        "To use Message Generation, you must have searched for profiles from the Prospect Finder page.\n\n"
        "1. **Profile Selection**\n"
        "   - Select profiles returned by Prospect Finder.\n"
        "   - Confirm selections by viewing profile information.\n\n"
        "2. **Message Generation**\n"
        "   - Search for relevant customer success stories to add to your message.\n"
        "   - Select a message template to use.\n"
        "   - Generate and download your messages.\n"
    )

with st.expander(label="What does the 'Search Profiles' toggle in Prospect Finder do?"):
    st.write("---")
    st.markdown(
        "1. **Toggle ON - Profile Retrieval**\n"
        "   - Turn this toggle on to activate the Cortex Search function to retrieve profiles before sending them to the LLM.\n\n"

        "2. **Toggle OFF - Market/Domain Research**\n"
        "   - Turning this toggle off to query the LLM on information on the profiles retrieved, industry, domain, roles, or responsibilities of the profiles.\n"
    )



