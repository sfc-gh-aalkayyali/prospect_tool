from functions.helper_global import *
import os
import hashlib
import re
from datetime import datetime
init_session_state()
session = create_session()

message_types = {
    "Email": "email_prompt.txt",
    "Text": "text_prompt.txt",
    "LinkedIn": "linkedin_prompt.txt",
    "Call": "call_prompt.txt",
    "Meeting": "meeting_prompt.txt",
}

def hash_value(value):
    return hashlib.sha256(value.strip().encode()).hexdigest()

def check_password_requirements(password):
    return (
        len(password) >= 6 and
        re.search(r"\d", password) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
    )

def load_prompt(file_name):
    with open(f"src/prompts/{file_name}", "r") as f:
        content = f.read().strip().split("---")
        return content[0].strip(), content[1].strip() if len(content) > 1 else ""
    return "", ""

if (not st.session_state["logged_in"]) or (st.session_state["logged_in"] and st.session_state["username"] == 'guest'):
    st.markdown("<h1 style='text-align: center;'>Welcome to the Snowflake Prospecting Tool</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 16px;'>Helping AE's and SDR's send the right message, to the right person, at the right time.</p>", unsafe_allow_html=True)

    padding1, content, padding2 = st.columns([10, 80, 10])
    with content:
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        hint_questions = st.selectbox(label="Password Hint (for recovery)",options=["What was the color of your first car?", "What was the name of your first pet?", "What is your childhood nickname?", "What was the mascot of your high school?", "What was the first phone model you ever owned?", "What was the name of your childhood best friend?", "What was the first concert you attended?"])
        hint = st.text_input("Answer", label_visibility="collapsed", placeholder="Type your answer here...")

        if st.button("Create Account", use_container_width=True, type='primary'):
            if not new_username or not new_password or not confirm_password or not hint or not hint_questions:
                st.warning("All fields are required.")
            elif new_username.lower() == "guest":
                st.warning("Username cannot be 'guest'. Please choose another name.")
            elif new_username.lower() == "admin":
                st.warning("Username cannot be 'admin'. Please choose another name.")
            elif len(new_username) > 25:
                st.warning("Username must be a maximum of 25 characters.")
            elif new_password != confirm_password:
                st.warning("Passwords do not match.")
            elif not check_password_requirements(new_password):
                st.warning("Password must be at least 6 characters long and contain a number and a symbol.")
            else:
                check_user_query = f"SELECT username FROM USERS WHERE username = '{new_username}'"
                existing_users = session.sql(check_user_query).collect()

                if existing_users:
                    st.error("Username already exists. Please choose another.")
                else:
                    hashed_password = hash_value(new_password)
                    hashed_hint = hash_value(hint)
                    ## insert user
                    insert_query = """
                        INSERT INTO USERS (username, password, hint, last_login, hint_question) 
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
                    """

                    try:
                        session.sql(insert_query, params=[new_username, hashed_password, hashed_hint, hint_questions]).collect()
                        st.success(f"User '{new_username}' created successfully.")
                    except Exception as e:
                        st.error(f"Error creating user '{new_username}': {e}")
                    
                    st.toast(f"User for '{new_username}' successfully created!", icon="🎉")

                    ## create default templates
                    for template_name, prompt in message_types.items():
                        default_prompt, default_message = load_prompt(prompt)
                        template_id = str(uuid.uuid4())
                        current_timestamp = datetime.now()
                        
                        # Fix formatting for the template name
                        formatted_template_name = f"{new_username}'s {template_name} Template"

                        insert_query = """
                            INSERT INTO TEMPLATES (ID, USERNAME, NAME_OF_TEMPLATE, TYPE_OF_MESSAGE, USER_PROMPT, MESSAGE_TEXT, DATE_ADDED) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """

                        try:
                            session.sql(insert_query, params=[
                                template_id, new_username, formatted_template_name, template_name, default_prompt, default_message, current_timestamp
                            ]).collect()
                        except Exception as e:
                            st.error(f"Error inserting template '{formatted_template_name}': {e}")

                    st.toast(f"Default templates for user {new_username} successfully created!", icon="✅")


                    st.session_state["logged_in"] = True
                    st.session_state["username"] = new_username
                    st.session_state["last_login"] = "First time login!"
                    st.session_state["first_login"] = True

                    st.success(f"Account created! Welcome, {new_username}!")
                    st.rerun()
        if st.button("Go back to Login", use_container_width=True):
            st.switch_page("pages/Login.py")
            st.stop()