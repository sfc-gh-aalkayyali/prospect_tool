from functions.helper_global import *
from functions.helper_generation import *
from functions.helper_session import *
import pandas as pd
import streamlit as st
import uuid
import os
# with st.sidebar.expander("Message Generation Options"):
#     st.text_area("System Prompt:", value=st.session_state.message_system_prompt, height=300, key="updated_message_system_prompt")
#     if st.button("Submit System Prompt", use_container_width=True, key="message_system", type="primary"):
#         st.session_state.message_system_prompt = st.session_state.updated_message_system_prompt
#         st.success("Successfully Added Prompt")

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
                
PROMPT_DIR = "prompts"

def load_prompt(file_name):
    file_path = os.path.join(PROMPT_DIR, file_name)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip().split("---")
            return content[0].strip(), content[1].strip() if len(content) > 1 else ""
    return "", ""

message_types = {
    "Email": "email_prompt.txt",
    "Text": "text_prompt.txt",
    "LinkedIn": "linkedin_prompt.txt",
    "Call Bullet Points": "call_prompt.txt",
    "Meeting Bullet Points": "meeting_prompt.txt",
}

st.title(":speech_balloon: Message Generation")
st.markdown("---")

people_df = st.session_state.general_profiles

if not people_df.empty:  
    init_service_metadata()
    session = create_session()
    username = st.session_state["username"]
    init_config_options_generation()

    if st.sidebar.button("Clear Selections", use_container_width=True, type="secondary"):
        del st.session_state.service_metadata
        del st.session_state.generated_messages
        del st.session_state.uploaded_messages
        del st.session_state.customer_stories_docs
        del st.session_state.selected_customer_stories_docs
        st.session_state.customer_stories_docs = []
        st.session_state.uploaded_messages = ""
        st.session_state.general_profile_selection = []
        st.session_state.selected_customer_stories_docs = []
        st.rerun()
    
    st.markdown("### Profile Selection")
    people_df['Full Name'] = people_df['First Name'] + " " + people_df['Last Name']
    people_df = people_df.drop_duplicates(subset=['Full Name'])

    selected_names = st.multiselect("Select Profiles:", people_df['Full Name'].tolist(), default=(st.session_state.general_profile_selection), key="profile_selection")

    selected_profiles_df = people_df[people_df['Full Name'].isin(selected_names)]


    if not selected_profiles_df.empty:
        with st.container(height=300):
            for index, row in selected_profiles_df.iterrows():
                profile_details = "\n".join([f"{col}: {val}" for col, val in row.items() if col not in ["Full Name"]])
                st.text_area(f"Profile: {row['Full Name']}", value=profile_details, height=200)

        # ✅ Only show this section if at least one profile is selected
        if selected_profiles_df.shape[0] > 0:
            st.markdown("---")
            st.markdown("### Customer Success Stories")
            col1, col2 = st.columns([0.6, 0.4])

            with col1:
                st.text_input("Search Keyword", placeholder="Enter keyword...", key="customer_stories_search")
            with col2:
                st.multiselect("Select Industry", ["Telecommunication"], key="customer_stories_filter")

            st.slider("Limit stories retrieved", min_value=1, max_value=8, value=3, key="customer_stories_limit")

            def find_stories():
                if st.session_state.customer_stories_search:
                    results, search_column = query_stories_cortex_search_service(
                        st.session_state.customer_stories_search,
                        st.session_state.customer_stories_filter or None,
                        st.session_state.customer_stories_limit
                    )
                    st.session_state.customer_stories_docs = [r[search_column] for r in results]

            if st.button("Find Customer Stories", use_container_width=True):
                find_stories()

            if st.session_state.customer_stories_docs != []:
                formatted_stories = [p.replace("\n", "<br>") for p in st.session_state.customer_stories_docs]
                st.write("Customer Stories")
                with st.container(height=300):
                    for i, story in enumerate(formatted_stories, start=1):
                        with st.container(height=200):
                            selected = st.checkbox(f"Select Customer Story {i}", key=f"story_key{i}")
                            st.markdown(f"{story}", unsafe_allow_html=True)
                        if selected and story not in st.session_state.selected_customer_stories_docs:
                            st.session_state.selected_customer_stories_docs.append(story)
                        elif not selected and story in st.session_state.selected_customer_stories_docs:
                            st.session_state.selected_customer_stories_docs.remove(story)

            st.markdown("---")
            st.markdown("### Customize & Save Template")

            message_type = st.selectbox("Message Type", list(message_types.keys()))

            template_name = st.text_input("Template Name", key="new_template_name", max_chars=30, placeholder="Type here...")

            default_prompt, default_message = load_prompt(message_types[message_type])

            col1, col2 = st.columns([0.5, 0.5])
            with col1:
                user_prompt = st.text_area("Customize Prompt", value=default_prompt, height=250, placeholder="Type here...")
            with col2:
                message_text = st.text_area("Customize Message", value=default_message, height=250, placeholder="Type here...")

            if st.session_state["logged_in"] and username != "guest":
                if st.button("Save Template", use_container_width=True):
                    if not template_name.strip():
                        st.warning("Please enter a name for the template before saving.")
                    elif not user_prompt.strip() or not message_text.strip():
                        st.warning("Please enter both a prompt and message before saving.")
                    else:
                        template_id = str(uuid.uuid4())
                        escaped_prompt, escaped_message = user_prompt.replace("'", "''"), message_text.replace("'", "''")

                        insert_query = f"""
                            INSERT INTO TEMPLATES (ID, USERNAME, NAME_OF_TEMPLATE, TYPE_OF_MESSAGE, USER_PROMPT, MESSAGE_TEXT)
                            VALUES ('{template_id}', '{username}', '{template_name}', '{message_type}', '{escaped_prompt}', '{escaped_message}')
                        """
                        try:
                            session.sql(insert_query).collect()
                            st.success(f"{message_type} Template '{template_name}' saved!")
                        except Exception as e:
                            st.error(f"Error saving template: {e}")
            else:
                if st.button("Log in or create an account to save templates.", use_container_width=True):
                    st.session_state["message_generation_show_confirm"] = True

                if st.session_state.message_generation_show_confirm:
                    st.error("⚠ If you continue, this will take you to the homepage to login or register and you will lose all chat history. Do you want to continue? ⚠")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Continue", use_container_width=True):
                            st.session_state.clear()
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancel", use_container_width=True):
                            st.session_state.message_generation_show_confirm = False
                            st.rerun()
            
            st.markdown("---")

            
            # if st.button(label="Add Sample Email", use_container_width=True):
            #     st.session_state.uploaded_messages = uploaded_files
            #     st.success("Successfully Added Email")
            if st.button("Generate Messages", type="primary", use_container_width=True):
                with st.spinner("Generating messages..."):
                    generated_messages = {
                        f"{row['First Name']} {row['Last Name']}": complete_function(create_direct_message(row.to_dict()))
                        for _, row in selected_profiles_df.iterrows()
                    }
                    st.session_state.generated_messages = generated_messages

            if st.session_state.get("generated_messages"):
                st.markdown("#### Generated Messages")
                all_messages = ""
                with st.container(height=300): 
                    for name, message in st.session_state.generated_messages.items():
                        col1, col2 = st.columns([0.9, 0.1])
                        with col1:
                            st.text_area(f"{name}:", value=message, height=300, placeholder="Type here...")
                        with col2:
                            st.download_button("📥", data=message, file_name=f"{name.replace(' ', '_')}_message.txt", mime="text/plain", key=f"download_{name}")

                        all_messages += f"---\n{name}:\n{message}\n\n"

                if all_messages:
                    st.download_button("📥 Download All Messages", data=all_messages, file_name="all_generated_messages.txt", mime="text/plain", use_container_width=True, key="download_all")
else:
    st.warning("Please search for profiles before using this feature.")    
    if st.button("Go to Prospect Finder", use_container_width=True):
        st.switch_page("pages/Prospect_Finder.py")
    if st.button("Go to Chat Manager", use_container_width=True):
        st.switch_page("pages/Chat_History.py")