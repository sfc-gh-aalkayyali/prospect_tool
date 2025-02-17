import streamlit as st
import json
from snowflake.cortex import complete, CompleteOptions
from docx import Document
from functions.helper_global import *
import streamlit.components.v1 as components
import re
    
def table_complete_function(prompt):
    prompt_json = json.dumps(prompt)

    response = complete(
        model=st.session_state.selected_model,
        prompt=prompt_json,
        options=CompleteOptions(
            temperature=st.session_state.temperature,
            top_p=st.session_state.top_p
        ),
        session=session
    )

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

def create_prompt_general(user_question):
    if st.session_state.use_chat_history:
        chat_history = get_general_chat_history()
        if chat_history != []:
            question_summary = make_chat_history_summary(chat_history, user_question)
            st.session_state.general_chat_history = question_summary.replace("$", "\$")
            results, search_column = query_cortex_search_service(question_summary, st.session_state.general_filters, st.session_state.general_num_retrieved_chunks)
            context_str = ""
            for i, r in enumerate(results, start=1):
                context_str += f"Context document {i}: {r[search_column]} \n" + "\n"
                st.session_state.general_people.append(r[search_column])
            
        else:
            results, search_column = query_cortex_search_service(user_question, st.session_state.general_filters, st.session_state.general_num_retrieved_chunks)
            context_str = ""
            for i, r in enumerate(results, start=1):
                context_str += f"Context document {i}: {r[search_column]} \n" + "\n"
                st.session_state.general_people.append(r[search_column])
    else:
        results, search_column = query_cortex_search_service(user_question, st.session_state.general_filters, st.session_state.general_num_retrieved_chunks)
        context_str = ""
        for i, r in enumerate(results, start=1):
            context_str += f"Context document {i}: {r[search_column]} \n" + "\n"
            st.session_state.general_people.append(r[search_column])
        chat_history = ""

    system_prompt = st.session_state.general_system_prompt
    user_prompt = f"""
[INST]
<chat_history>
{chat_history}
</chat_history>
<context>
{context_str}
</context>
<question>
{user_question}
</question>
[/INST]
""".strip()
    prompt = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    return prompt