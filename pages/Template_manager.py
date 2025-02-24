import streamlit as st
import uuid
import os
from functions.helper_global import *
from datetime import datetime


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

st.title("📌 Manage Saved Templates & Prompts")
st.markdown("---")

# col1, col2 = st.columns([0.5, 0.5])

# with col1:


session = create_session()

if "logged_in" not in st.session_state or not st.session_state["logged_in"] or st.session_state["username"] == "guest":
    st.warning("Please log in or register to manage or create templates.")
    if st.button("Login or Register", use_container_width=True):
        st.session_state["template_manager_show_confirm"] = True

    if st.session_state.template_manager_show_confirm:
        st.error("⚠ If you continue, this will take you to the homepage to login or register and you will lose all chat history. Do you want to continue? ⚠")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Continue", use_container_width=True):
                st.session_state.clear()
                st.rerun()
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.template_manager_show_confirm = False
                st.rerun()
    st.stop()

username = st.session_state["username"]

def load_prompt(file_name):
    file_path = os.path.join("prompts", file_name)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip().split("---")
            return content[0].strip(), content[1].strip() if len(content) > 1 else ""
    return "", ""

message_types = {
    "Email": "email_prompt.txt",
    "Text": "text_prompt.txt",
    "LinkedIn": "linkedin_prompt.txt",
    "Call": "call_prompt.txt",
    "Meeting": "meeting_prompt.txt",
}

st.markdown("### Create a New Template")

message_type = st.selectbox("Message Type", list(message_types.keys()), key="new_template_type")

template_name = st.text_input("Template Name", key="new_template_name", max_chars=100, value=f"{username}'s {message_type} Template", placeholder="Type here...")

default_prompt, default_message = load_prompt(message_types[message_type])

col1, col2 = st.columns([0.5, 0.5])

with col1:
    user_prompt = st.text_area("Customize Prompt", value=default_prompt, height=200, key="new_template_prompt", placeholder="Type here...", help="To ensure your output is as expected, follow a similiar template for your prompt.\n\nPlease include explanations of the following tags:\n\n - <profile> and </profile> tags for linkedin profile information.\n\n - <example> and  </example> tags for the sample message/template.\n\n - <story> and </story> tags for the customer success stories.\n\n\n\n - <battlecard> and </battlecard> tags for the comeptitor battle cards.\n\nIt is crucial that this information is included in your prompt so that the AI model can understand what is being fed into it.")
with col2:
    message_text = st.text_area("Customize Message", value=default_message, height=200, key="new_template_text", placeholder="Type here...", help="You can add any example or previous message you have sent to a prospective customer.\n\nThis will allow the AI model to follow a similar structure and writing style to your sample message/template.")

if st.button("Save New Template", use_container_width=True, type="primary"):
    if not template_name.strip():
        st.warning("Please enter a name for the template before saving.")
    elif not user_prompt.strip() or not message_text.strip():
        st.warning("Please enter both a prompt and message before saving.")
    else:
        # Check if a template with the same name already exists
        query = """
            SELECT ID FROM TEMPLATES 
            WHERE NAME_OF_TEMPLATE = ? 
            AND USERNAME = ?
        """

        try:
            existing_template = session.sql(query, params=[template_name, username]).collect()
        except Exception as e:
            st.error(f"Error retrieving template: {e}")

        if existing_template:
            # Template exists: Update it
            template_id = existing_template[0][0]  # Get the existing template ID

            update_query = """
                UPDATE TEMPLATES 
                SET USER_PROMPT = ?, 
                    MESSAGE_TEXT = ?, 
                    DATE_ADDED = CURRENT_TIMESTAMP
                WHERE ID = ? AND USERNAME = ?
            """
            
            try:
                session.sql(update_query, params=[user_prompt, message_text, template_id, username]).collect()
                st.success(f"Template '{template_name}' updated successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Error updating template: {e}")


        else:
            template_id = str(uuid.uuid4())
            current_timestamp = datetime.now()

            insert_query = """
                INSERT INTO TEMPLATES (ID, USERNAME, NAME_OF_TEMPLATE, TYPE_OF_MESSAGE, USER_PROMPT, MESSAGE_TEXT, DATE_ADDED)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            try:
                session.sql(insert_query, params=[template_id, username, template_name, message_type, user_prompt, message_text, current_timestamp]).collect()
                st.success(f"New template '{template_name}' saved successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving template: {e}")



st.markdown("---")
st.markdown("### Your Saved Templates")

query = f"""
        SELECT * 
        FROM TEMPLATES 
        WHERE USERNAME = ?
        ORDER BY DATE_ADDED
    """

templates = session.sql(query, params=[username]).collect()

if not templates:
    st.info("You have no templates yet.")
else:
    st.text_input("Search Templates", key='template_search', placeholder="Type to search...").strip().lower()

    filtered_templates = [template for template in templates if st.session_state.template_search in template["NAME_OF_TEMPLATE"].lower()]

    if st.session_state.template_search and not filtered_templates:
        st.warning("No templates found.")
        if st.button("Reset Search", key="reset_template_search", use_container_width=True):
            if st.session_state.template_search:
                del st.session_state.template_search
                st.session_state.template_search = ''
                st.rerun()
    if filtered_templates:
        with st.container(height=350):  
            for row in filtered_templates:
                template_id, username, template_name, message_type, user_prompt, message_text, date_added = row

                with st.expander(f"{template_name} ({message_type} Template)"):
                    updated_name = st.text_input("Template Name", template_name, key=f"edit_name_{template_id}")
                    updated_prompt = st.text_area("Edit Prompt", user_prompt, key=f"edit_prompt_{template_id}", height=150)
                    updated_message = st.text_area("Edit Message", message_text, key=f"edit_message_{template_id}", height=150)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Update", key=f"update_{template_id}", use_container_width=True):
                            try:
                                update_query = """
                                    UPDATE TEMPLATES 
                                    SET NAME_OF_TEMPLATE = ?, 
                                        USER_PROMPT = ?, 
                                        MESSAGE_TEXT = ?
                                    WHERE ID = ? AND USERNAME = ?
                                """
                                session.sql(update_query, params=[
                                    updated_name, 
                                    updated_prompt, 
                                    updated_message, 
                                    template_id, 
                                    username
                                ]).collect()
                                
                                st.success(f"Updated template: {updated_name}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating template: {e}")
                    with col2:
                        if st.button("Delete", key=f"delete_{template_id}", use_container_width=True):
                            try:
                                delete_query = "DELETE FROM TEMPLATES WHERE ID = ? AND USERNAME = ?"
                                session.sql(delete_query, params=[template_id, username]).collect()
                                
                                st.success(f"Deleted template: {template_name}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting template: {e}")

if st.button("Go to Message Generator", use_container_width=True):
    st.switch_page("pages/Message_Generation.py")