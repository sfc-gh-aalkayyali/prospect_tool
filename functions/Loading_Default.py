import os
from functions.helper_global import *
from datetime import datetime

message_types = {
    "Email": "email_prompt.txt",
    "Text": "text_prompt.txt",
    "LinkedIn": "linkedin_prompt.txt",
    "Call": "call_prompt.txt",
    "Meeting": "meeting_prompt.txt",
}

def load_prompt(file_name):
    file_path = os.path.join("prompts", file_name)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip().split("---")
            return content[0].strip(), content[1].strip() if len(content) > 1 else ""
    return "", ""


for template_name, prompt in message_types.items():
    default_prompt, default_message = load_prompt(prompt)
    template_id = str(uuid.uuid4())
    current_timestamp = datetime.now()

    # Fix formatting for the template name
    formatted_template_name = f"{template_name} Template (Default)"

    insert_query = """
        INSERT INTO TEMPLATES (ID, USERNAME, NAME_OF_TEMPLATE, TYPE_OF_MESSAGE, USER_PROMPT, MESSAGE_TEXT, DATE_ADDED) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    try:
        session.sql(insert_query, params=[
            template_id, 'guest', formatted_template_name, template_name, default_prompt, default_message, current_timestamp
        ]).collect()
    except Exception as e:
        st.error(f"Error inserting template '{formatted_template_name}': {e}")