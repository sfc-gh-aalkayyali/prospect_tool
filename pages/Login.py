import streamlit as st
import hashlib
import re
from datetime import datetime
from functions.helper_global import *

session = create_session()
init_session_state()

def hash_value(value):
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

if "allow_reset" not in st.session_state:
    st.session_state.allow_reset = False

if "new_password" not in st.session_state:
    st.session_state.new_password = ""

if "failed_attempts" not in st.session_state:
    st.session_state.failed_attempts = 0

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state["logged_in"]:
    st.session_state.setdefault("snowflake", False)

    st.markdown("<h1 style='text-align: center;'>Welcome to the Snowflake Prospecting Tool</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 16px;'>Helping AE's and SDR's send the right message, to the right person, at the right time.</p>", unsafe_allow_html=True)
    if not st.session_state.snowflake:
        st.snow()
        st.session_state.snowflake = True
        
    padding1, content, padding2 = st.columns([10, 80, 10])
    with content:
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
        if st.button("Register", use_container_width=True):
            st.switch_page("pages/Register.py")
            st.stop()

    if st.session_state["failed_attempts"] >= 3:
        with content:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("Reset Password")
            reset_username = st.text_input("Enter your username to reset password")

            if st.button("Check username", use_container_width=True):
                query = f"SELECT hint_question, hint FROM USERS WHERE username = '{reset_username}'"
                result = session.sql(query).collect()

                if result:
                    hint_question = result[0]["HINT_QUESTION"] if "HINT_QUESTION" in result[0].as_dict() else None
                    stored_hashed_hint = result[0]["HINT"] if "HINT" in result[0].as_dict() else None

                    if hint_question:
                        st.session_state["reset_username"] = reset_username
                        st.session_state["hint_question"] = hint_question
                        st.session_state["stored_hashed_hint"] = stored_hashed_hint
                        st.session_state["hint_verified"] = False  # Reset verification state

                    else:
                        st.error("No hint question set for this user. Please contact support.")
                else:
                    st.error("Username not found.")

            # Display hint question if username is verified
            if "hint_question" in st.session_state:
                reset_hint = st.text_input(f"{st.session_state['hint_question']}", 
                                        placeholder="Enter your answer here...", 
                                        key="reset_hint")

                if st.button("Submit Hint Answer", use_container_width=True):
                    if reset_hint.strip():
                        if hash_value(reset_hint) == st.session_state["stored_hashed_hint"]:
                            st.session_state["hint_verified"] = True  # Allow password reset
                            st.success("Hint verified successfully. Please set a new password.")
                        else:
                            st.error("Incorrect hint answer.")
                    else:
                        st.warning("Please enter an answer to the hint question.")

            # Show password reset fields only if hint is verified
            if st.session_state.get("hint_verified", False):
                new_reset_password = st.text_input("Enter new password", type="password")
                confirm_reset_password = st.text_input("Confirm new password", type="password")

                if st.button("Reset Password", use_container_width=True):
                    if new_reset_password and confirm_reset_password:
                        if new_reset_password == confirm_reset_password:
                            if check_password_requirements(new_reset_password):
                                hashed_new_password = hash_value(new_reset_password)
                                update_query = f"UPDATE USERS SET password = '{hashed_new_password}' WHERE username = '{st.session_state['reset_username']}'"
                                session.sql(update_query).collect()
                                st.success("Password reset successfully. Please log in.")
                                st.session_state["failed_attempts"] = 0
                                st.rerun()
                            else:
                                st.warning("Password must be at least 6 characters long and contain a number and a symbol.")
                        else:
                            st.warning("Passwords do not match.")
                    else:
                        st.warning("Please fill in both password fields.")