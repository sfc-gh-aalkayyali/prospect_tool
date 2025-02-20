from functions.helper_global import *
from functions.helper_generation import *
from functions.helper_session import *
import pandas as pd
import streamlit as st
import uuid
import os

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

if "message_type" not in st.session_state:
    st.session_state.message_type = list(message_types.keys())[0]

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
        st.session_state.selected_customer_stories_docs = []

        if st.session_state.profile_selection:
            del st.session_state.profile_selection
            st.session_state.profile_selection = []

        if st.session_state.customer_stories_company:
            del st.session_state.customer_stories_company
            st.session_state.customer_stories_company = []

        if st.session_state.customer_stories_industry:
            del st.session_state.customer_stories_industry
            st.session_state.customer_stories_industry = []

        if st.session_state.message_type:
            del st.session_state.message_type
            st.session_state.message_type = list(message_types.keys())[0]


        st.rerun()
    
    st.markdown("### Profile Selection")
    people_df['Full Name'] = people_df['First Name'] + " " + people_df['Last Name']
    people_df = people_df.drop_duplicates(subset=['Full Name'])

    selected_names = st.multiselect("Select Profiles:", people_df['Full Name'].tolist(), default=st.session_state.profile_selection)

    st.session_state.profile_selection = selected_names

    selected_profiles_df = people_df[people_df['Full Name'].isin(selected_names)]

    if not selected_profiles_df.empty:
        with st.container(height=300):
            for index, row in selected_profiles_df.iterrows():
                profile_details = "\n".join([f"{col}: {val}" for col, val in row.items() if col not in ["Full Name"]])
                st.text_area(f"Profile: {row['Full Name']}", value=profile_details, height=200)

        st.markdown("---")
        st.markdown("### Customer Success Stories (OPTIONAL)")
        col1, col2 = st.columns([0.6, 0.4])

        with col1:
            st.text_input("Search Keyword", placeholder="Enter keyword...", key="customer_stories_search")
            st.slider("Limit stories retrieved", min_value=1, max_value=20, value=3, key="customer_stories_limit")
        with col2:
            industries = session.sql('SELECT DISTINCT INDUSTRY FROM LINKEDIN.PUBLIC."STORIES"').to_pandas()
            industries = industries.dropna().loc[industries['INDUSTRY'].astype(str).str.strip() != '']
            selected_industries = st.multiselect("Select Industry (OPTIONAL)", industries,  default=st.session_state.customer_stories_industry)
            st.session_state.customer_stories_industry = selected_industries

            companies = session.sql('SELECT DISTINCT COMPANY_NAME FROM LINKEDIN.PUBLIC."STORIES"').to_pandas()
            companies = companies.dropna().loc[companies['COMPANY_NAME'].astype(str).str.strip() != '']
            selected_companies = st.multiselect("Select Company (OPTIONAL)", companies, default=st.session_state.customer_stories_company)
            st.session_state.customer_stories_company = selected_companies

        
        def find_stories():
            if st.session_state.customer_stories_docs != []:
                del st.session_state.customer_stories_docs
                
            if st.session_state.customer_stories_search and st.session_state.customer_stories_search.strip() != '':
                results, search_column = query_stories_cortex_search_service(
                    st.session_state.customer_stories_search
                )
                st.session_state.customer_stories_docs = [r[search_column] for r in results]
            else:
                st.warning("You must enter a keyword search")

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

        st.session_state.message_type = st.selectbox(
            "Message Type", 
            list(message_types.keys()), 
            index=list(message_types.keys()).index(st.session_state.message_type)  # Keep the previous selection
        )


        template_name = st.text_input("Template Name", key="new_template_name", max_chars=30, value=f"{username}'s {st.session_state.message_type} Template",placeholder="Type here...")

        default_prompt, default_message = load_prompt(message_types[st.session_state.message_type])

        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            system_prompt = st.text_area("Customize Prompt", value=default_prompt, height=250, placeholder="Type here...", help="To ensure your output is as expected, follow a similiar template for your prompt.\n\nPlease include explanations of the following tags:\n\n - <profile> and </profile> tags for linkedin profile information.\n\n - <example> and  </example> tags for the sample message/template.\n\n - <story> and </story> tags for the customer success stories.\n\n It is crucial that this information is included in your prompt so that the AI model can understand what is being fed into it.")
            st.session_state.system_prompt = system_prompt
        with col2:
            message_text = st.text_area("Customize Message", value=default_message, height=250, placeholder="Type here...", help="You can add any example or previous message you have sent to a prospective customer.\n\nThis will allow the AI model to follow a similar structure and writing style to your sample message/template.")
            st.session_state.sample_message = message_text

        if st.session_state["logged_in"] and username != "guest":
            if st.button("Save Template", use_container_width=True):
                if not template_name.strip():
                    st.warning("Please enter a name for the template before saving.")
                elif not system_prompt.strip() or not message_text.strip():
                    st.warning("Please enter both a prompt and message before saving.")
                else:
                    template_id = str(uuid.uuid4())

                    try:
                        # Use parameterized query to prevent syntax errors
                        insert_query = """
                            INSERT INTO TEMPLATES (ID, USERNAME, NAME_OF_TEMPLATE, TYPE_OF_MESSAGE, USER_PROMPT, MESSAGE_TEXT)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """
                        session.sql(insert_query, params=[template_id, username, template_name, st.session_state.message_type, system_prompt, message_text]).collect()
                        
                        st.success(f"{st.session_state.message_type} Template '{template_name}' saved!")
                    
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

        if st.button("Generate Messages", type="primary", use_container_width=True):
            if st.session_state.system_prompt and st.session_state.sample_message and st.session_state.system_prompt.strip() != '' and st.session_state.sample_message.strip() != '':
                with st.spinner("Generating messages..."):
                    generated_messages = {
                        f"{row['First Name']} {row['Last Name']}": complete_function(create_direct_message(row.to_dict()))
                        for _, row in selected_profiles_df.iterrows()
                    }
                    st.session_state.generated_messages = generated_messages
            else:
                st.warning("Please input a prompt and sample message to generate messages.")

            

        if st.session_state.get("generated_messages"):
            st.markdown("---")
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
                st.download_button("Download All Messages", data=all_messages, file_name="all_generated_messages.txt", mime="text/plain", use_container_width=True, key="download_all")
    else:
        st.info("Please select one or more profiles from the dropdown.")
else:
    st.warning("Please search for profiles before using this feature.")    
    if st.button("Go to Prospect Finder", use_container_width=True):
        st.switch_page("pages/Prospect_Finder.py")
    if st.session_state.logged_in and st.session_state.username != 'guest':
        if st.button("Go to Chat Manager", use_container_width=True):
            st.switch_page("pages/Chat_History.py")