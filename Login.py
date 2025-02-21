import streamlit as st
import time

st.set_page_config(page_title="Snowflake Prospecting Tool", page_icon="🔍", layout="wide")

import hashlib
import re
import os
from datetime import datetime
from functions.helper_global import *

session = create_session()
init_session_state()

def hash_value(value):
    """Hashes a given value using SHA-256."""
    return hashlib.sha256(value.strip().encode()).hexdigest()

def check_password_requirements(password):
    return (
        len(password) >= 6 and
        re.search(r"\d", password) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
    )

def check_password(plain_password, stored_hashed_password):
    return hash_value(plain_password) == stored_hashed_password.strip()

def update_last_login(username):
    last_login_time = datetime.now()
    session.sql(f"UPDATE USERS SET last_login = '{last_login_time}' WHERE username = '{username}'").collect()

def get_last_login(username):
    result = session.sql(f"SELECT last_login FROM USERS WHERE username = '{username}'").collect()
    return result[0][0] if result and result[0][0] else "First time login!"

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

if not st.session_state["logged_in"]:
    st.session_state.setdefault("snowflake", False)

    hide_sidebar_style = """
    <style>
        [data-testid="stSidebar"] {display: none;}
    </style>
    """
    st.markdown(hide_sidebar_style, unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Welcome to the Snowflake Prospecting Tool</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 16px;'>Helping AE's and SDR's send the right message, to the right person, at the right time.</p>", unsafe_allow_html=True)
    if not st.session_state.snowflake:
        st.snow()
        st.session_state.snowflake = True
        
    padding1, content, padding2 = st.columns([25, 50, 25])
    with content:
        tabs = st.tabs(["Login", "Register"])

        with tabs[0]:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login", use_container_width=True, type='primary'):
                if username and password:
                    query = f"SELECT password FROM USERS WHERE username = '{username}'"
                    result = session.sql(query).collect()

                    if result:
                        stored_hashed_password = result[0][0]
                        if check_password(password.strip(), stored_hashed_password):
                            update_last_login(username)
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = username
                            st.session_state["last_login"] = get_last_login(username)
                            st.session_state["first_login"] = False
                            st.session_state["failed_attempts"] = 0
                            st.success(f"Welcome back, {username}!")
                            st.rerun()
                        else:
                            st.session_state["failed_attempts"] += 1
                            if st.session_state["failed_attempts"] >= 3:
                                st.error("Too many failed attempts. You may want to reset your password.")
                            else:
                                st.error("Incorrect password.")
                    else:
                        st.error("Username not found.")
                else:
                    st.warning("Please enter both username and password.")

            if st.button("Continue as Guest", use_container_width=True):
                st.session_state["logged_in"] = True
                st.session_state["username"] = "guest"
                st.session_state["last_login"] = "Guest users don't have saved history."
                st.session_state["first_login"] = False
                st.success("Logged in as Guest.")
                st.rerun()

        with tabs[1]:
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            hint = st.text_input("Password Hint (for recovery)")

            if st.button("Create Account", use_container_width=True, type='primary'):
                if not new_username or not new_password or not confirm_password or not hint:
                    st.warning("All fields are required.")
                elif new_username.lower() == "guest":
                    st.warning("Username cannot be 'guest'. Please choose another name.")
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
                            INSERT INTO USERS (username, password, hint, last_login) 
                            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        """

                        try:
                            session.sql(insert_query, params=[new_username, hashed_password, hashed_hint]).collect()
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

    if st.session_state["failed_attempts"] >= 3:
        with content:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("Reset Password")
            reset_username = st.text_input("Enter your username to reset password")
            new_reset_password = st.text_input("Enter new password", type="password")
            reset_hint = st.text_input("Enter your password hint")

            if st.button("Reset Password", use_container_width=True):
                query = f"SELECT hint FROM USERS WHERE username = '{reset_username}'"
                result = session.sql(query).collect()

                if result:
                    stored_hashed_hint = result[0][0]
                    if hash_value(reset_hint) == stored_hashed_hint:
                        if check_password_requirements(new_reset_password):
                            hashed_new_password = hash_value(new_reset_password)
                            update_query = f"UPDATE USERS SET password = '{hashed_new_password}' WHERE username = '{reset_username}'"
                            session.sql(update_query).collect()
                            st.success("Password reset successfully. Please log in.")
                            st.session_state["failed_attempts"] = 0
                            st.rerun()
                        else:
                            st.warning("Password must be at least 6 characters long and contain a number and a symbol.")
                    else:
                        st.error("Incorrect password hint.")
                else:
                    st.error("Username not found.")
elif st.session_state["logged_in"] and st.session_state["username"] != 'guest':
    expand_sidebar_script = """
    <script>
        let sidebar = window.parent.document.querySelector("[data-testid='stSidebar']");
        if (sidebar) { sidebar.style.display = "block"; }
    </script>
    """
    st.markdown(expand_sidebar_script, unsafe_allow_html=True)

    pages = {
        "Navigation Pages": [
            st.Page("pages/Home.py", title="Home"),
            st.Page("pages/Prospect_Finder.py", title="Prospect Finder"),
            st.Page("pages/Message_Generation.py", title="Message Generation"),
            st.Page("pages/Chat_History.py", title="Chat History"),
            st.Page("pages/Template_Manager.py", title="Template Manager"),
            st.Page("pages/Customer_Stories.py", title="Customer Story Manager"),
            st.Page("pages/Battle_Cards.py", title="Battle Cards Manager"),
        ]
    }
    pg = st.navigation(pages)
    pg.run()

else:
    expand_sidebar_script = """
    <script>
        let sidebar = window.parent.document.querySelector("[data-testid='stSidebar']");
        if (sidebar) { sidebar.style.display = "block"; }
    </script>
    """
    st.markdown(expand_sidebar_script, unsafe_allow_html=True)

    pages = {
        "Navigation Pages": [
            st.Page("pages/Home.py", title="Home"),
            st.Page("pages/Prospect_Finder.py", title="Prospect Finder"),
            st.Page("pages/Message_Generation.py", title="Message Generation"),
        ]
    }
    pg = st.navigation(pages)
    pg.run()
