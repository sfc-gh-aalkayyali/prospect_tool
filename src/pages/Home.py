import streamlit as st
from functions.helper_global import *
init_session_state()

cols = st.columns([85,15])
with cols[1]:
    if st.session_state.username != "guest":
        if st.button("Logout", use_container_width=True):
            logout()
    else:
        if st.button("Login", use_container_width=True):
            st.session_state.login_show_confirm = True

with cols[0]:
    if st.session_state.login_show_confirm:
        st.warning("⚠ You will be redirected you to the homepage to login or register and you will lose all chat history. ⚠")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅", use_container_width=True):
                logout()
        with col2:
            if st.button("❌", use_container_width=True):
                st.session_state.login_show_confirm = False
                st.rerun()

st.title(":snowboarder: Home")

st.markdown("---")

col1, col2 = st.columns(2, gap='large')

with col1:
    with st.container(border= False):
        st.subheader(":mag: Prospect Finder")
        st.write(
            "This page allows you to search for prospects, research into their industries, roles, responsibilites, and more all powered by AI.\n\n"
            "Use filters, extract prospect linkedin profile data, query the LLM."
        )
        if st.button("Go to Prospect Finder", key="page1_btn", use_container_width=True, type="primary"):
            st.switch_page("pages/Prospect_Finder.py")

with col2:
    with st.container(border=False):
        st.subheader(":speech_balloon: Message Generation")
        st.write(
            "This page allows you to generate automated outreach emails, meeting notes, linkedin messages, and more all powered by AI. \n\n"
            "Choose profiles, customer success stories, add your personalized messages."
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

with st.expander(label="How does Chat History Work?"):
    st.write("---")
    st.markdown(
        "To use Chat History, you must have previously searched for profiles from the Prospect Finder page.\n\n"
        "1. **Select a Saved Chat**\n"
        "   - Select one your previous chats from the drop down to view.\n"
        "2. **View Selected Saved Chat**\n"
        "   - View your saved chat.\n"
        "   - Continue your chat where you left off by clicking on the 'Continue Chat' button.\n" 
    )

with st.expander(label="How does Template Manager Work?"):
    st.write("---")
    st.markdown(
        "This page allows you to manage templates to use for message generation.\n"
        "You can create, delete, or modify your templates and use them in the 'Message Generation' page.\n"
        "By default, each new account will have an email, call, meeting, linkedin, and text message template.\n"
        "Only you will be able to see your templates, no other user can access these.\n"
        "1. **Create a New Template**\n"
        "   - Select the type of template you want to create, for example email, text, linkedin, etc..\n"
        "   - Customize the system prompt, this will direct the LLM on how to structure its output, please follow the guidelines by hovering over the '?' icon to the right of the textbox.\n"
        "   - Customize the message that will be fed into the LLM as an example to follow. It is perferable that you paste in a message you have previously used with prospects.\n"
        "   - Save the template and go to the 'Message Generation' page to use it.\n"
        "2. **Manage Your Templates**\n"
        "   - Search for the template you want to manage.\n"
        "   - Click on the template to alter the name, prompt, or message.\n"
        "   - Click on the 'Update' button to save your changes, or 'Delete' to remove your template.\n"
    )

with st.expander(label="How does Customer Story Manager Work?"):
    st.write("---")
    st.markdown(
        "This page allows you to manage Customer Stories to use for message generation.\n"
        "You can create, delete, or modify your Customer Stories and use them in the 'Message Generation' page.\n"
        "Customer Stories you create will be accessable to all users, however only you will be able to edit or delete them.\n"
        "Similarly, any Customer Story created by another user will be available for you to use. However only the owner will be able to edit or delete them.\n"
        "1. **Create a New Customer Story**\n"
        "   - Add the name of the customer you want to add a success story for.\n"
        "   - Add the industry of the customer you want to add a success story for.\n"
        "   - Add the details of the Customer Story, make sure to add in metrics on how Snowflake has made an impact on their busienss.\n"
        "2. **Manage Your Customer Story**\n"
        "   - Search for the Customer Story you want to manage.\n"
        "   - Click on the Customer Story to alter the name, prompt, or message.\n"
        "   - Click on the 'Update' button to save your changes, or 'Delete' to remove your Customer Story.\n"
    )


with st.expander(label="How does Battle Cards Manager Work?"):
    st.write("---")
    st.markdown(
        "This page allows you to manage Battle Cards to use for message generation.\n"
        "You can create, delete, or modify your Battle Cards and use them in the 'Message Generation' page.\n"
        "Battle Cards you create will be accessable to all users, however only you will be able to edit or delete them.\n"
        "Similarly, any Battle Card created by another user will be available for you to use. However only the owner will be able to edit or delete them.\n"
        "1. **Create a New Battle Card**\n"
        "   - Add the name of the Battle Card you want to add.\n"
        "   - Add the industry of the Battle Card.\n"
        "   - Add the details for the Battle Card.\n"
        "2. **Manage Your Customer Story**\n"
        "   - Search for the Battle Card you want to manage.\n"
        "   - Click on the Battle Card to alter the name, prompt, or message.\n"
        "   - Click on the 'Update' button to save your changes, or 'Delete' to remove your Battle Card.\n"
    )

with st.expander(label="What does the 'Search Profiles' toggle in Prospect Finder do?"):
    st.write("---")
    st.markdown(
        "1. **Toggle ON - Profile Retrieval**\n"
        "   - Turn this toggle on to activate the Cortex Search function to retrieve profiles before sending them to the LLM.\n\n"

        "2. **Toggle OFF - Market/Domain Research**\n"
        "   - Turning this toggle off to query the LLM on information on the profiles retrieved, industry, domain, roles, or responsibilities of the profiles.\n"
    )