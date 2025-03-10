import streamlit as st
from functions.helper_session import *
from snowflake.core import Root
import pandas as pd
import streamlit as st
import uuid
import io
import re
import time
from snowflake.cortex import Complete, CompleteOptions

session = create_session()
root = Root(session)

def init_session_state():
    """Initialize all required session state variables."""
    for key, default_value in [
        ("general_messages", []),
        ("generated_messages", []),
        ("general_chat_history", ""),
        ("clear_conversation", False),
        ("general_people", []),
        ("profile_selection", []),
        ("customer_stories_industry", []),
        ("selected_prompt", None),
        ("general_profiles", pd.DataFrame()),
        ("customer_stories_docs", []),
        ("uploaded_emails", ""),
        ("chat_id", uuid.uuid4()),
        ("uploaded_messages", ""),
        ("username", "guest"),
        ("first_login", True),
        ("failed_attempts", 0),
        ("logged_in", False),
        ("message_generation_show_confirm", False),
        ("template_manager_show_confirm", False),
        ("chat_history_show_confirm", False),
        ("login_show_confirm", False),
        ("selected_customer_stories_docs", []),
        ("battlecards_manager_show_confirm", False),
        ("selected_battlecards", []),
        ("battle_card_industry", []),
        ("battle_card_company", []),
        ("customer_battle_cards", []),
        ("selected_battle_cards", []),
        ("temperature", 0.5),
        ("top_p", 0.9),
        ("thumbs_button", False),
        ("feedback_submitted", False),
        ("generated_profiles", []),
        ("feedback_text", ''),
        ("feedback_error", '')]:
        if key not in st.session_state:
            st.session_state[key] = default_value
            
def init_service_metadata():
    """
    Initialize the session state for cortex search service metadata. Query the available
    cortex search services from the Snowflake session and store their names and search
    columns in the session state.
    """

    if "service_metadata" not in st.session_state:
        services = session.sql("SHOW CORTEX SEARCH SERVICES;").collect()
        service_metadata = {}

        if services:
            for s in services:
                svc_name = s["name"].lower()
                svc_search_col = session.sql(
                    f"DESC CORTEX SEARCH SERVICE {svc_name};"
                ).collect()[0]["search_column"]
                service_metadata[svc_name] = svc_search_col

        st.session_state.service_metadata = service_metadata


def query_cortex_search_service(query):
    db, schema = session.get_current_database(), session.get_current_schema()

    cortex_search_service = (
        root.databases[db]
        .schemas[schema]
        .cortex_search_services["linkedin_service"]
    )

    # Build the filters dynamically
    filters = []

    # Location filter
    if st.session_state.location_filter:
        filters.append({
            "@or": [{"@eq": {"LOCATION": loc}} for loc in st.session_state.location_filter]
        })

    # Industry filter
    if st.session_state.industry_filter:
        filters.append({
            "@or": [{"@eq": {"INDUSTRY": ind}} for ind in st.session_state.industry_filter]
        })

    # Company filter
    if st.session_state.company_filter:
        filters.append({
            "@or": [{"@eq": {"COMPANYNAME": comp}} for comp in st.session_state.company_filter]
        })

    # Classification filter
    if st.session_state.classification_filter:
        filters.append({
            "@or": [{"@eq": {"CLASSIFICATION": cls}} for cls in st.session_state.classification_filter]
        })

    # Connection degree filter
    if st.session_state.connectiondegree_filter:
        filters.append({
            "@or": [{"@eq": {"CONNECTIONDEGREE": cls}} for cls in st.session_state.connectiondegree_filter]
        })


    # Combine filters using @and if multiple filters exist
    filters_dict = {"@and": filters} if filters else {}

    # Perform the search with filters if present
    context_documents = cortex_search_service.search(
        query, columns=[], filter=filters_dict, limit=st.session_state.general_num_retrieved_chunks
    )

    results = context_documents.results
    service_metadata = st.session_state.service_metadata
    search_col = service_metadata.get("linkedin_service")

    return results, search_col

def query_battle_cards_cortex_search_service(query):
    db, schema = session.get_current_database(), session.get_current_schema()

    cortex_search_service = (
        root.databases[db]
        .schemas[schema]
        .cortex_search_services["battlecard"]
    )

    filters = []


    if st.session_state.battle_card_industry:
        filters.append({
            "@or": [{"@eq": {"INDUSTRY": cls}} for cls in st.session_state.battle_card_industry]
        })

    if st.session_state.battle_card_company:
        filters.append({
            "@or": [{"@eq": {"COMPANY_NAME": cls}} for cls in st.session_state.battle_card_company]
        })

    filters_dict = {"@and": filters} if filters else {}

    context_documents = cortex_search_service.search(
        query, columns=[], filter=filters_dict, limit=st.session_state.battle_card_limit
    )

    results = context_documents.results
    service_metadata = st.session_state.service_metadata
    search_col = service_metadata.get("battlecard")
    return results, search_col

def remove_think_tags(text):
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

def query_stories_cortex_search_service(query):
    db, schema = session.get_current_database(), session.get_current_schema()

    cortex_search_service = (
        root.databases[db]
        .schemas[schema]
        .cortex_search_services["stories"]
    )

    filters = []


    if st.session_state.customer_stories_industry:
        filters.append({
            "@or": [{"@eq": {"INDUSTRY": cls}} for cls in st.session_state.customer_stories_industry]
        })

    filters_dict = {"@and": filters} if filters else {}

    context_documents = cortex_search_service.search(
        query, columns=[], filter=filters_dict, limit=st.session_state.customer_stories_limit
    )

    results = context_documents.results
    service_metadata = st.session_state.service_metadata
    search_col = service_metadata.get("stories")
    return results, search_col

def get_general_chat_history():
    start_index = max(
        0, len(st.session_state.general_messages) - st.session_state.num_chat_messages
    )
    return st.session_state.general_messages[start_index : len(st.session_state.general_messages) - 1]

def make_chat_history_summary(chat_history, question):

    if chat_history: 
        with open("src/prompts/chat_history_prompt.txt", "r") as file:
            system_prompt = file.read()

        user_prompt = f"""
[INST]
<chat_history>
{chat_history}
</chat_history>
<question>
{question}
</question>
[/INST]
        """
        prompt = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        summary = complete_function(prompt)
        st.session_state.general_chat_history = summary
    else:
        summary = ""

    return summary

@st.cache_data
def text_download(text):
    if not text:
        return None

    # Create a BytesIO object and write the text to it
    text_bytesio = io.BytesIO()
    text_bytesio.write(text.encode('utf-8'))
    text_bytesio.seek(0)  # Reset pointer to the start of the file for reading

    return text_bytesio

def remove_think_tags(text):
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

def complete_function(prompt):

    response = Complete(model=st.session_state.selected_model, prompt=prompt, options=CompleteOptions(temperature=st.session_state.temperature, top_p=st.session_state.top_p), session=session)
    
    if st.session_state.selected_model == 'deepseek-r1':
        return remove_think_tags(response)
    else:
        return response

def logout():
    st.session_state.clear()
    st.rerun()