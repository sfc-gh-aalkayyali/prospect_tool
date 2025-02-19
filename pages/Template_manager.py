import streamlit as st
import uuid
import os
from functions.helper_global import create_session


st.title("📌 Manage Saved Templates & Prompts")

col1, col2 = st.columns([0.5, 0.5])

with col1:
    if st.button("⬅ Back to Message Generator", use_container_width=True):
        st.switch_page("pages/Message_generation.py")

with col2:
    if st.button("🔑 Login", use_container_width=True):
        st.switch_page("Home.py")

session = create_session()

if "logged_in" not in st.session_state or not st.session_state["logged_in"] or st.session_state["username"] == "guest":
    st.warning("🔒 Please log in to manage or create templates.")
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


st.markdown("---")
st.markdown("### 📝 Create a New Template")

message_type = st.selectbox("📨 Message Type", list(message_types.keys()), key="new_template_type")

default_prompt, default_message = load_prompt(message_types[message_type])

col1, col2 = st.columns([0.5, 0.5])
with col1:
    user_prompt = st.text_area("📝 Customize Prompt", value=default_prompt, height=200, key="new_template_prompt")
with col2:
    message_text = st.text_area("📩 Customize Message", value=default_message, height=200, key="new_template_text")

if st.button("💾 Save New Template", use_container_width=True):
    if not user_prompt.strip() or not message_text.strip():
        st.warning("⚠️ Please enter both a prompt and message before saving.")
    else:
        template_id = str(uuid.uuid4())
        escaped_prompt = user_prompt.replace("'", "''")
        escaped_message = message_text.replace("'", "''")

        insert_query = f"""
            INSERT INTO TEMPLATES (ID, USERNAME, NAME_OF_TEMPLATE, TYPE_OF_MESSAGE, USER_PROMPT, MESSAGE_TEXT)
            VALUES ('{template_id}', '{username}', '{message_type} Template', '{message_type}', '{escaped_prompt}', '{escaped_message}')
        """
        try:
            session.sql(insert_query).collect()
            st.success(f"✅ Template '{message_type} Template' saved!")
        except Exception as e:
            st.error(f"❌ Error saving template: {e}")


st.markdown("---")
st.markdown("### 🗂 Your Saved Templates")

try:
    saved_templates = session.sql(f"""
        SELECT ID, NAME_OF_TEMPLATE, TYPE_OF_MESSAGE, USER_PROMPT, MESSAGE_TEXT 
        FROM TEMPLATES 
        WHERE USERNAME = '{username}'
    """).collect()

    if not saved_templates:
        st.info("💡 No saved templates found. Create one above.")
    else:
        with st.container(height=400):  
            for row in saved_templates:
                template_id, template_name, message_type, user_prompt, message_text = row

                if f"edit_mode_{template_id}" not in st.session_state:
                    st.session_state[f"edit_mode_{template_id}"] = False

                with st.expander(f"📌 {template_name} ({message_type})", expanded=False):
                    if st.session_state[f"edit_mode_{template_id}"]:
                        st.markdown("#### ✏ Edit Template")

                        col1, col2 = st.columns([0.5, 0.5])
                        with col1:
                            new_prompt = st.text_area("🔹 Edit Prompt", value=user_prompt, key=f"edit_prompt_{template_id}", height=150)
                        with col2:
                            new_message = st.text_area("🔹 Edit Message", value=message_text, key=f"edit_message_{template_id}", height=150)

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("💾 Save", key=f"save_{template_id}", use_container_width=True):
                                escaped_prompt = new_prompt.replace("'", "''")
                                escaped_message = new_message.replace("'", "''")

                                update_query = f"""
                                    UPDATE TEMPLATES 
                                    SET USER_PROMPT = '{escaped_prompt}', MESSAGE_TEXT = '{escaped_message}'
                                    WHERE ID = '{template_id}' AND USERNAME = '{username}'
                                """
                                try:
                                    session.sql(update_query).collect()
                                    st.success(f"✅ {template_name} updated!")
                                    st.session_state[f"edit_mode_{template_id}"] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error updating template: {e}")

                        with col2:
                            if st.button("❌ Cancel", key=f"cancel_edit_{template_id}", use_container_width=True):
                                st.session_state[f"edit_mode_{template_id}"] = False
                                st.rerun()

                    else:
                        st.markdown("#### 📄 Template Preview")
                        st.markdown(f"**📢 Prompt:**\n> {user_prompt}")
                        st.markdown(f"**📩 Message:**\n> {message_text}")

                        col1, col2, col3 = st.columns([0.4, 0.4, 0.2])
                        with col1:
                            if st.button("✏ Edit", key=f"edit_{template_id}", use_container_width=True):
                                st.session_state[f"edit_mode_{template_id}"] = True
                                st.rerun()

                        with col2:
                            if st.button("🗑 Delete", key=f"delete_{template_id}", use_container_width=True):
                                delete_query = f"DELETE FROM TEMPLATES WHERE ID = '{template_id}' AND USERNAME = '{username}'"
                                try:
                                    session.sql(delete_query).collect()
                                    del st.session_state[f"edit_mode_{template_id}"]
                                    st.success(f"❌ {template_name} deleted!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error deleting template: {e}")

except Exception as e:
    st.error(f"⚠ Error fetching templates: {e}")
