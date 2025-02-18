import streamlit as st
import json
from snowflake.cortex import Complete, CompleteOptions
from docx import Document
from functions.helper_global import *
import streamlit.components.v1 as components
import re

def init_config_options_finder():
    st.session_state.selected_cortex_search_service = "LINKEDIN_SERVICE"

    with st.sidebar.expander("LLM Options"):
        st.toggle("Use chat history", key="use_chat_history", value=True)
        st.selectbox(
            "Select LLM Model",
            ("llama3.1-70b", "mistral-large2"),
            key="selected_model", help="*It is recommended to choose llama3.1-70*"
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
            value=0.5,
            key="temperature",
            step=0.1,
            min_value=0.0,
            max_value=1.0,
            help=f"""*Higher temperature will result in more creative, diverse, but potentially less coherent outputs. Conversely, lower temperature makes the model more predictable, conservative, and focused. 
Changing the temperature affects how likely the model is to select less probable tokens during text generation. 
Temperature is a scaling factor applied to the predicted probabilities of tokens. A temperature of 1 leaves the probabilities unchanged, while a temperature below 1 sharpens the distribution, making the most probable tokens even more likely to be selected.*""")
        
        st.slider(
            "Top_p/Creativity",
            value=0.0,
            key="top_p",
            step=0.1,
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
    prompt_json = json.dumps(prompt)

    response = Complete(model=st.session_state.selected_model, prompt=prompt_json, options=CompleteOptions(temperature=st.session_state.temperature, top_p=st.session_state.top_p), session=session)    
    response = response.strip()

    if response.startswith("No profiles returned.") or response.startswith("An error occurred:"):
        return response

    # Split individual profiles
    profiles = re.split(r"\n\s*---\s*\n", response)

    # Extract fields from each profile
    data = [extract_fields(profile) for profile in profiles]

    # Convert to DataFrame
    df = pd.DataFrame(data).fillna('')

    return df

FIELD_PATTERNS = {
    "First Name": re.compile(r"First Name:\s*(.+)"),
    "Last Name": re.compile(r"Last Name:\s*(.+)"),
    "Location": re.compile(r"Location:\s*(.+)"),
    "Shared Connections": re.compile(r"Shared Connections:\s*(\d+)"),
    "Title": re.compile(r"Title:\s*(.+)"),
    "Classification": re.compile(r"Classification:\s*(.+?)(?:\n|$)"),
    "Company": re.compile(r"Company:\s*(.+)"),
    "Industry": re.compile(r"Industry:\s*(.+)"),
    "Connection Degree": re.compile(r"Connection Degree:\s*(.+)"),
    "Duration in Role": re.compile(r"Duration in Role:\s*(.+?)\s+in role"),
    "Duration in Company": re.compile(r"Duration in Company:\s*(.+)"),
    "LinkedIn Profile URL": re.compile(r"LinkedIn Profile URL:\s*(.+)"),
    "Title Description": re.compile(r"Title Description:\s*(.+)"),
    "Summary": re.compile(r"Summary:\s*(.+)")
}

def extract_fields(profile):
    extracted = {}
    for field, pattern in FIELD_PATTERNS.items():
        match = pattern.search(profile)
        if match:
            extracted[field] = match.group(1).strip()
    return extracted

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
        context_str += f"Context document {i}: {r[search_column]} \n" + "\n"
        st.session_state.general_people.append(r[search_column])

    with open("prompts/table_system_prompt.txt", "r") as file:
        system_prompt = file.read()

    user_prompt = f"""
[INST]
{chat_history}
<profile>
{context_str}
</profile>
<question>
{user_question}
</question>
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

    if st.session_state.general_people:
        context = f"""
<profile>
{st.session_state.general_people}
</profile>
"""
    else:
        context = ""

    with open("prompts/query_system_prompt.txt", "r") as file:
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