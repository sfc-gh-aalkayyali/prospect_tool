import streamlit as st
from functions.helper_session import *
from snowflake.core import Root
import pandas as pd
import streamlit as st
import json
import uuid
import io
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
        ("general_profile_selection", []),
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
        ("selected_customer_stories_docs", []),
("marketing_message", """
Hi [Name],


I noticed Telstra's efforts to expand in-house gen AI solutions to improve customer interactions, including "One Sentence Summary" and "Ask Telstra". Leveraging data and AI for customer understanding and personalisation is clearly a top strategic priority for you. 


I'm part of the account team at Snowflake which supports Telstra. Given your role, I thought you might be interested in the work we're doing at Spark NZ, using AI to hyper-personalise experiences on the data cloud, increasing marketing message conversions by 20x and reducing marketing spend by 16%. 


If this sounds interesting, would it be a terrible use of time to explore how we might do the same for Telstra? 


How is your availability on Wednesday at 3pm or 4pm for a 20/30 minute intro on Teams?


Cheers,
""".strip()),
("ESG_message", """
Hey [Name],


Your role in Performance and Strategy and previous experience in energy prompted me to reach out. Are you involved with ESG initiatives at Telstra? 


The reason I ask is because Snowflake has a data marketplace with dozens of ESG datasets maintained by other companies. You can get access and report on these in real-time. This could help you to cut costs and hit your ESG and energy consumption targets. 


Telstra Health have recently onboarded Snowflake and we're having conversations across the larger Telstra organisation. It would be great to introduce you to the Snowflake account team who can provide a tailored discussion and explain what we're doing with similar businesses to help with their ESG targets. 


Are you free on Thursday afternoon for a 20/30 minute Teams? The team is based in Melbourne if you'd be open to a coffee instead. 


Best,
""".strip()),
("message_system_prompt", f"""
Context:
The user is an employee at Snowflake, a cloud-based data platform providing scalable storage, processing, and analytics for structured and semi-structured data. Snowflake enables cost efficiency and high performance by separating compute from storage. It allows multiple workloads to run concurrently without performance degradation and supports real-time data sharing across organizations. The platform natively handles formats like JSON and Parquet and features built-in security, governance, and compliance capabilities for robust data protection. Snowflake automates scaling, optimization, and maintenance, requiring minimal management while delivering reliability for data warehousing, business intelligence, and machine learning.

The user needs to reach out to individuals at Telstra, Australia’s largest telecommunications company, offering services like broadband, 5G, cloud solutions, and enterprise networks. Telstra is a leader in IoT, AI, and cybersecurity and focuses on innovation to deliver reliable connectivity and digital solutions for diverse industries.

Your Role:
You are a professional AI chat assistant tasked with drafting personalized outreach emails to Telstra employees. 
These emails should:
    1) Highlight how Snowflake’s capabilities align with the individual’s role and Telstra’s business objectives.
    2) Emphasize key differentiators such as:
        - Real-time data sharing across organizations.
        - Native multi-cloud support for flexibility and cost optimization.
        - Scalable, automated management to reduce operational overhead.
        - Advanced analytics for business intelligence and machine learning.
        - Strong security, governance, and compliance for sensitive data handling.
    3) Mirror the tone, structure, and style of example emails provided between <email> and </email> tags.
    4) Base personalisation on LinkedIn profile information provided between <profile> and </profile> tags.
    5) If you are provided with customer success stories between <story> and </story> tags, include their stories in your email.
    6) If you are given the chat history between the <chat_history> and </chat_history> tags, take the chat history into account before generating the message.


Task:
When provided with an individual’s LinkedIn profile and example emails, craft a concise, compelling, and personalised outreach email. Focus on how Snowflake’s solutions can benefit the individual’s role at Telstra, referencing specific skills, projects, or interests from their profile where relevant.
    1) Personalization: Make the email feel tailored to the recipient by referencing their role, achievements, or challenges they might face.
    2) Relevance: Emphasize how Snowflake can support Telstra’s goals in telecommunications, innovation, data analytics, and digital transformation.
    3) Structure & Tone: Follow the professional yet approachable tone and concise structure demonstrated in the example emails.
    4) Evidence: Demonstrate how Snowflake has helped other customers in their domain by incorporating other customer success stories if provided.
    5) Chat History: Take chat history with the Snowflake employee into account as context before generating an outreach email.


Output Requirements:
    1) Only output the final email, fully polished and ready to send, with no additional explanations or placeholders.
    2) Ensure the email closely follows the style of the example provided, focusing on clarity, personalization, and alignment with Telstra’s objectives.
    3) Include customer success stories if provided to you to demonstrate how Snowflake has helped customers in their domain.
    4) Do not add an email Subject header, only the email body.
""".strip()),
("splunk_message", """
Hi [Name],


I noticed your role as Senior Cybersecurity Architect at Telstra and it prompted me to reach out. 


By way of introduction, I support the Telstra team here at Snowflake. Given your role as Senior Cybersecurity Architect, I thought you might be interested in how Snowflake integrates with Splunk, providing more than 50% cost savings.


We hear cybersecurity teams using Splunk often face similar challenges related to cost, scalability and usability.


Snowflake leverages our platform for security analytics to reduce SIEM costs while enabling more proactive risk management, simplifying compliance, and detecting sophisticated threats.


The best part is that you can retain Splunk and use Snowflake as a security lake only. Cost savings can be up to 90%, eliminating data egress costs and providing you faster access to your data.


If the time permits, I’d love to schedule 30 minutes in the calendar to discuss how we could replicate this at Telstra. How is your availability next Wednesday? 


Best,
""".strip()),
("email_placeholder", "")]:
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


def query_stories_cortex_search_service(query, filters, input_limit):
    db, schema = session.get_current_database(), session.get_current_schema()

    cortex_search_service = (
        root.databases[db]
        .schemas[schema]
        .cortex_search_services["stories"]
    )

    if filters:
        filters_dict = {
            "@or": [{"@eq": {"Industry": f}} for f in filters]
        }
            
        context_documents = cortex_search_service.search(
            query, columns=[],   filter = filters_dict, limit=input_limit
        )
    else:
        context_documents = cortex_search_service.search(
            query, columns=[], limit=input_limit
        )
    results = context_documents.results

    service_metadata = st.session_state.service_metadata
    # search_col = [s["search_column"] for s in service_metadata
    #                 if s["name"] == "STORIES"][0]
    
    search_col = service_metadata.get("stories")

    return results, search_col

def get_general_chat_history():
    start_index = max(
        0, len(st.session_state.general_messages) - st.session_state.num_chat_messages
    )
    return st.session_state.general_messages[start_index : len(st.session_state.general_messages) - 1]

def make_chat_history_summary(chat_history, question):

    if chat_history: 
        with open("prompts/chat_history_prompt.txt", "r") as file:
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

def complete_function(prompt):

    response = Complete(model="llama3.1-70b", prompt=prompt, options=CompleteOptions(temperature=st.session_state.temperature, top_p=st.session_state.top_p), session=session)
    
    return response  

def logout():
    st.session_state.clear()
    st.rerun()