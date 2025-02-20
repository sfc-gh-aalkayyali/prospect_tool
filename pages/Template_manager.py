import streamlit as st
import uuid
import os
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


st.markdown("### Create a New Template")

message_type = st.selectbox("Message Type", list(message_types.keys()), key="new_template_type")

template_name = st.text_input("Template Name", key="new_template_name", max_chars=30, placeholder="Type here...")

default_prompt, default_message = load_prompt(message_types[message_type])

col1, col2 = st.columns([0.5, 0.5])

with col1:
    user_prompt = st.text_area("Customize Prompt", value=default_prompt, height=200, key="new_template_prompt", placeholder="Type here...")
with col2:
    message_text = st.text_area("Customize Message", value=default_message, height=200, key="new_template_text", placeholder="Type here...")

if st.button("Save New Template", use_container_width=True):
    if not template_name.strip():
        st.warning("Please enter a name for the template before saving.")
    elif not user_prompt.strip() or not message_text.strip():
        st.warning("Please enter both a prompt and message before saving.")
    else:
        template_id = str(uuid.uuid4())
        escaped_template_name = template_name.replace("'", "''")
        escaped_prompt = user_prompt.replace("'", "''")
        escaped_message = message_text.replace("'", "''")

        insert_query = f"""
            INSERT INTO TEMPLATES (ID, USERNAME, NAME_OF_TEMPLATE, TYPE_OF_MESSAGE, USER_PROMPT, MESSAGE_TEXT)
            VALUES ('{template_id}', '{username}', '{escaped_template_name}', '{message_type}', '{escaped_prompt}', '{escaped_message}')
        """
        try:
            session.sql(insert_query).collect()
            st.success(f"Template '{template_name}' saved")
            st.rerun()
        except Exception as e:
            st.error(f"Error saving template: {e}")



st.markdown("---")
st.markdown("### Your Saved Templates")

try:
    saved_templates = session.sql(f"""
        SELECT ID, NAME_OF_TEMPLATE, TYPE_OF_MESSAGE, USER_PROMPT, MESSAGE_TEXT 
        FROM TEMPLATES 
        WHERE USERNAME = '{username}'
    """).collect()

    if not saved_templates:
        st.info("No saved templates found. Create one above.")
    else:
        with st.container(height=350):  
            for row in saved_templates:
                template_id, template_name, message_type, user_prompt, message_text = row

                if f"edit_mode_{template_id}" not in st.session_state:
                    st.session_state[f"edit_mode_{template_id}"] = False

                with st.expander(f"{template_name} ({message_type} Template)", expanded=False):
                    if st.session_state[f"edit_mode_{template_id}"]:
                        col1, col2 = st.columns([0.5, 0.5])

                        with col1:
                            new_template_name = st.text_input(
                                "Template Name", 
                                value=template_name, 
                                key=f"edit_name_{template_id}", 
                                max_chars=30
                            )
                            new_prompt = st.text_area("Edit Prompt", value=user_prompt, key=f"edit_prompt_{template_id}", height=150, placeholder="Type here...")

                        with col2:
                            new_message = st.text_area("Edit Message", value=message_text, key=f"edit_message_{template_id}", height=150, placeholder="Type here...")

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Save", key=f"save_{template_id}", use_container_width=True):
                                escaped_name = new_template_name.replace("'", "''")
                                escaped_prompt = new_prompt.replace("'", "''")
                                escaped_message = new_message.replace("'", "''")

                                update_query = f"""
                                    UPDATE TEMPLATES 
                                    SET NAME_OF_TEMPLATE = '{escaped_name}', 
                                        USER_PROMPT = '{escaped_prompt}', 
                                        MESSAGE_TEXT = '{escaped_message}'
                                    WHERE ID = '{template_id}' AND USERNAME = '{username}'
                                """
                                try:
                                    session.sql(update_query).collect()
                                    st.success(f"{escaped_name} updated")
                                    st.session_state[f"edit_mode_{template_id}"] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating template: {e}")

                        with col2:
                            if st.button("Cancel", key=f"cancel_edit_{template_id}", use_container_width=True):
                                st.session_state[f"edit_mode_{template_id}"] = False
                                st.rerun()

                    else:
                        st.markdown(f"<u><b>Prompt:</b></u><br>{user_prompt}", unsafe_allow_html=True)
                        st.markdown("---")
                        st.markdown(f"<u><b>Message:</b></u><br>{message_text}", unsafe_allow_html=True)
                        col1, col2, col3 = st.columns([0.4, 0.4, 0.2])

                        with col1:
                            if st.button("Edit", key=f"edit_{template_id}", use_container_width=True):
                                st.session_state[f"edit_mode_{template_id}"] = True
                                st.rerun()

                        with col2:
                            if st.button("Delete", key=f"delete_{template_id}", use_container_width=True):
                                delete_query = f"DELETE FROM TEMPLATES WHERE ID = '{template_id}' AND USERNAME = '{username}'"
                                try:
                                    session.sql(delete_query).collect()
                                    del st.session_state[f"edit_mode_{template_id}"]
                                    st.success(f"{template_name} deleted")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting template: {e}")

except Exception as e:
    st.error(f"Error fetching templates: {e}")

if st.button("Go to Message Generator", use_container_width=True):
    st.switch_page("pages/Message_Generation.py")