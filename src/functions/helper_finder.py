import streamlit as st
import json
from snowflake.cortex import Complete, CompleteOptions
from docx import Document
from functions.helper_global import *
import streamlit.components.v1 as components
import re
import copy


def init_config_options_finder():
    st.session_state.selected_cortex_search_service = "LINKEDIN_SERVICE"

    with st.sidebar.expander("LLM Options"):
        st.toggle("Use chat history", key="use_chat_history", value=True)

        # Selectbox using session state
        st.selectbox(
            "Select LLM Model",
            ("llama3.1-70b", "deepseek-r1"),
            key="selected_model"
        )

        st.slider(
        "Select number of messages to use in chat history",
        value=5,
        key="num_chat_messages",
        min_value=1,
        max_value=10,
        help="*Limits the number of chats for the LLM to consider as context during a conversation.*"
    )
        st.slider(
            "Temperature/Creativity",
            value=st.session_state.temperature,
            step=0.1,
            min_value=0.0,
            max_value=1.0,
            help=f"""*Higher temperature will result in more creative, diverse, but potentially less coherent outputs. Conversely, lower temperature makes the model more predictable, conservative, and focused. 
Changing the temperature affects how likely the model is to select less probable tokens during text generation. 
Temperature is a scaling factor applied to the predicted probabilities of tokens. A temperature of 1 leaves the probabilities unchanged, while a temperature below 1 sharpens the distribution, making the most probable tokens even more likely to be selected.*""")
        
        st.slider(
            "Top_p/Creativity",
            step=0.1,
            value=st.session_state.top_p,
            min_value=0.0,
            max_value=1.0,
            help=f"""*Higher Top_p will result in a wider range of words considered, leading to more varied results. Conversely lower top_p leads to a narrower range of words considered, focusing on the most likely options. 
Changing the top_p affects affects the range of tokens the model can select from during text generation.
When top_p is 1, the model considers all possible tokens. As you decrease the top_p value, only the most probable tokens that together make up the top p% of the probability mass are included, while the rest are discarded.*"""
        )

        if st.session_state.general_chat_history != "":
            with st.container(height=150):
                st.write("Chat History")
                st.markdown(st.session_state.general_chat_history)

def table_complete_function(prompt):
    if st.session_state.selected_model == 'deepseek-r1':
        response = remove_think_tags(Complete(model=st.session_state.selected_model, prompt=prompt, options=CompleteOptions(temperature=st.session_state.temperature, top_p=st.session_state.top_p), session=session))
    else:
        response = Complete(model=st.session_state.selected_model, prompt=prompt, options=CompleteOptions(temperature=st.session_state.temperature, top_p=st.session_state.top_p), session=session)
    
    response = response.strip()

    if response.startswith("I don't know the answer to that question.") or response.startswith("An error occurred:"):
        return response

    print(response)
    # Split individual profiles
    profiles = re.split(r" \| ", response)

    placeholders = ", ".join(["?"] * len(profiles))
    # Correct SQL query using parameterized binding
    query = f"""
        SELECT * FROM LINKEDIN.PUBLIC."LinkedIn Accounts" 
        WHERE UNIQUE_ID IN ({placeholders})
    """

    # Execute query with parameter binding (passing the list correctly)
    df = session.sql(query, params=profiles).to_pandas()

    df = df[[
    "FULLNAME", "COMPANYNAME", "INDUSTRY", "TITLE",  
    "CLEANED_CLASSIFICATION", "LOCATION", "TITLEDESCRIPTION", 
    "SUMMARY", "LINKEDINPROFILEURL", "DURATIONINROLE", 
    "DURATIONINCOMPANY", "CONNECTIONDEGREE", "SHAREDCONNECTIONSCOUNT"
]].rename(columns={
    "FULLNAME": "Full Name",
    "COMPANYNAME": "Company Name",
    "INDUSTRY": "Industry",
    "TITLE": "Job Title",
    "CLEANED_CLASSIFICATION": "Classification",
    "LOCATION": "Location",
    "TITLEDESCRIPTION": "Job Description",
    "SUMMARY": "Profile Summary",
    "LINKEDINPROFILEURL": "LinkedIn URL",
    "DURATIONINROLE": "Duration In Role",
    "DURATIONINCOMPANY": "Duration At Company",
    "CONNECTIONDEGREE": "Connection Degree",
    "SHAREDCONNECTIONSCOUNT": "Shared Connections"
})
    return df


def convert_to_int(value):
    """Converts numeric strings to integers, handling missing or invalid values."""
    try:
        return int(value) if str(value).strip().isdigit() else 0 
    except (ValueError, TypeError):
        return 0

import re

def convert_duration_to_months(duration):
    if not isinstance(duration, str) or duration.strip() == "":
        return 0  # Return 0 if duration is empty or not a string

    # Normalize input by removing unnecessary words
    duration = re.sub(r"in role|in company", "", duration, flags=re.IGNORECASE).strip().lower()

    # Extract all numeric values
    numbers = list(map(int, re.findall(r"\d+", duration)))  # Extracts all numbers

    # Find occurrences of 'year', 'month' in any order
    years_match = re.search(r"(?:years?|yrs?)", duration)
    months_match = re.search(r"(?:months?|mos?)", duration)

    # Assign values based on order of numbers found
    years = numbers[0] if years_match and numbers else 0
    months = numbers[1] if months_match and len(numbers) > 1 else 0

    return (years * 12) + months


def get_slider_range(df, column_name, default_max=100):
    """Returns a valid (min, max) tuple for a slider."""
    if column_name in df.columns and not df[column_name].empty:
        min_value = int(df[column_name].min())
        max_value = int(df[column_name].max())
    else:
        min_value, max_value = 0, default_max  # Default if column is missing or empty

    # Ensure max is greater than min
    if min_value == max_value:
        max_value += 1

    return min_value, max_value


@st.cache_data
def text_download(text):
    """Converts text to a downloadable file format."""
    return io.BytesIO(text.encode('utf-8'))

def read_txt(file):
    """Read text from a .txt file"""
    return file.read().decode('utf-8')

def read_docx(file):
    """Read text from a .docx file"""
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def create_table_prompt(user_question):
    if st.session_state.use_chat_history:
        history = make_chat_history_summary(get_general_chat_history(), user_question)
        chat_history = f"""
<chat_history>
{history}
</chat_history>
"""
    else:
        chat_history = ""

    results, search_column = query_cortex_search_service(user_question)
    context_str = ""
    st.session_state.general_people = []
    for i, r in enumerate(results, start=1):
        context_str += f"<profile {i}>Context document {i}: {r[search_column]}</profile {i}>\n\n"
        st.session_state.general_people.append(r[search_column])
    
    with open("src/prompts/table_system_prompt.txt", "r") as file:
        system_prompt = file.read()

    user_prompt = f"""
[INST]
{chat_history}
<question>
{user_question}
</question>
{context_str}
[/INST]
""".strip()
    
    prompt = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    return prompt


def create_query_prompt(user_question):
    if st.session_state.use_chat_history:
        history = make_chat_history_summary(get_general_chat_history(), user_question)
        chat_history = f"""
<chat_history>
{history}
</chat_history>
"""
    else:
        chat_history = ""

    if st.session_state.generated_profiles and st.session_state.generated_profiles != []:
        context = f"""
<profile>
{st.session_state.generated_profiles}
</profile>
"""
    else:
        context = ""
        
    with open("src/prompts/query_system_prompt.txt", "r") as file:
        system_prompt = file.read()

    user_prompt = f"""
[INST]
{chat_history}
{context}
<question>
{user_question}
</question>
[/INST]
""".strip()
    prompt = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    return prompt

def remove_think_tags(text):
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

def generate_chat_title(chat_id, username, chat_history, session=session):
    if len(chat_history) == 0: 
        return "No Title"

    # Check if a chat with the same chat_id and username already exists
    existing_title_query = """
    SELECT CHAT_TITLE FROM CHAT_HISTORY WHERE CHAT_ID = ? AND USERNAME = ? LIMIT 1
    """
    result = session.sql(existing_title_query, params=[str(chat_id), username]).collect()

    if result:
        return result[0]["CHAT_TITLE"]  # Return existing title if chat exists

    # If no existing chat title is found, generate a new title
    with open("src/prompts/chat_history_title_prompt.txt", "r") as file:
        system_prompt = file.read()


    user_prompt = f"""
[INST]
<chat_history>
{chat_history}
</chat_history>
[/INST]
    """.strip()

    prompt = [
        {"role": "system", "content": system_prompt}, 
        {"role": "user", "content": user_prompt}
    ]

    return Complete(model="llama3.1-70b", prompt=prompt, options=CompleteOptions(temperature=0.0, top_p=0.0), session=session)

def save_chat(chat_date, username, chat_id, chat_title, chat_history, chat_summary, session=session):
    if not chat_history:
        return False
    
    try:
        unique_chat_str = str(chat_id)

        # Create a deep copy to avoid modifying the original chat_history
        chat_history_copy = copy.deepcopy(chat_history)

        # If chat_history is a DataFrame, convert it to JSON
        if isinstance(chat_history_copy, pd.DataFrame):
            chat_history_duplicate = chat_history_copy.to_json(orient="records")  # Convert DataFrame to JSON string

        # If chat_history is a list of dictionaries, check for embedded DataFrames
        elif isinstance(chat_history_copy, list):
            for message in chat_history_copy:
                if isinstance(message.get("content"), pd.DataFrame):
                    message["content"] = message["content"].to_json(orient="records")  # Convert DataFrame to JSON string

            chat_history_duplicate = json.dumps(chat_history_copy)
        
        elif isinstance(chat_history_copy, dict):
            chat_history_duplicate = json.dumps(chat_history_copy)
        
        elif isinstance(chat_history_copy, str):
            try:
                json.loads(chat_history_copy)  # Check if it's already valid JSON
            except json.JSONDecodeError:
                chat_history_duplicate = json.dumps({"chat": chat_history_copy})  # Wrap in JSON-compatible format
        
        merge_query = """
        MERGE INTO CHAT_HISTORY AS target
        USING (SELECT ? AS CHAT_DATE, ? AS USERNAME, ? AS CHAT_ID, ? AS CHAT_TITLE, ? AS CHAT_HISTORY, ? AS CHAT_SUMMARY) AS source
        ON target.CHAT_ID = source.CHAT_ID AND target.USERNAME = source.USERNAME
        WHEN MATCHED THEN
            UPDATE SET 
                CHAT_DATE = source.CHAT_DATE,
                CHAT_HISTORY = source.CHAT_HISTORY,
                CHAT_SUMMARY = source.CHAT_SUMMARY,
                CHAT_TITLE = target.CHAT_TITLE
        WHEN NOT MATCHED THEN
            INSERT (CHAT_DATE, USERNAME, CHAT_ID, CHAT_TITLE, CHAT_HISTORY, CHAT_SUMMARY)
            VALUES (source.CHAT_DATE, source.USERNAME, source.CHAT_ID, source.CHAT_TITLE, source.CHAT_HISTORY, source.CHAT_SUMMARY);
        """


        # Execute the query safely
        session.sql(merge_query, params=[chat_date, username, unique_chat_str, chat_title, chat_history_duplicate, chat_summary]).collect()
        return True

    except Exception as e:
        return False