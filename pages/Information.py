import streamlit as st

st.title(":information_source: Information")

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




