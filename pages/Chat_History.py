import streamlit as st
import pandas as pd
import json
from functions.helper_session import create_session
from functions.helper_global import *

st.title(":hourglass_flowing_sand: Chat History")

# Initialize session
session = create_session()

# Define icons for messages
icons = {"assistant": "🕵️‍♂️", "user": "👤"}

# Function to load chat history from database
def load_chat(username, session):
    try:
        query = """
        SELECT *
        FROM CHAT_HISTORY 
        WHERE USERNAME = ?
        ORDER BY CHAT_DATE DESC
        """
        chat_records = session.sql(query, params=[username]).collect()

        if not chat_records:
            return pd.DataFrame()

        chat_data = []
        for row in chat_records:
            try:
                chat_json_str = row.CHAT_HISTORY.strip()

                # Parse JSON safely
                messages = json.loads(chat_json_str) if chat_json_str else []

                # Ensure all messages have correctly formatted content
                updated_messages = []
                for message in messages:
                    if isinstance(message.get("content"), str):
                        try:
                            # Check if the string is valid JSON
                            content_json = json.loads(message["content"])

                            if isinstance(content_json, list) and all(isinstance(i, dict) for i in content_json):  
                                # If JSON string was actually a DataFrame-like list of dictionaries
                                df = pd.DataFrame(content_json)
                                message["content"] = df  # Convert back to DataFrame
                            else:
                                message["content"] = content_json  # Normal JSON conversion

                        except json.JSONDecodeError:
                            pass  # Leave as string if not valid JSON

                    updated_messages.append(message)

            except json.JSONDecodeError as e:
                updated_messages = []  # Default to empty on failure

            chat_data.append({
                "Chat ID": row.CHAT_ID,
                "Date": row.CHAT_DATE,
                "Title": row.CHAT_TITLE,
                "Chat Summary": row.CHAT_SUMMARY,
                "Messages": updated_messages
            })

        df = pd.DataFrame(chat_data)
        return df

    except Exception as e:
        return pd.DataFrame()


init_session_state()
if st.session_state.username != "guest":
    cols = st.columns([85,15])
    with cols[1]:
        if st.button("Logout", use_container_width=True):
            logout()

username = st.session_state.username

if username == "guest":
    st.warning("You must be logged in to view your chat history.")
    if st.button("Login or Register", use_container_width=True):
        st.session_state["chat_history_show_confirm"] = True

    if st.session_state.chat_history_show_confirm:
        st.error("⚠ If you continue, this will take you to the homepage to login or register and you will lose all chat history. Do you want to continue? ⚠")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Continue", use_container_width=True):
                st.session_state.clear()
                st.rerun()
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.chat_history_show_confirm = False
                st.rerun()
    st.stop()

chats = load_chat(username, session)

if chats.empty:
    st.warning("No previous chats found.")
    if st.button("Go to Prospect Finder", use_container_width=True):
        st.switch_page("pages/Prospect_Finder.py")

else:
    # Display chat history without Messages column
    chat_history_df = pd.DataFrame(chats, columns=["Chat ID", "Date", "Title", "Chat Summary", "Messages"])
    chat_history_df["Date"] = pd.to_datetime(chat_history_df["Date"]).dt.strftime("%Y-%m-%d %H:%M")

    # Select a chat to continue
    selected_chat = st.selectbox("Select a chat to continue:", chat_history_df["Title"].tolist())

    st.dataframe(chat_history_df.drop(columns=["Messages"]), hide_index=True, use_container_width=True)

    if selected_chat:
        chat_row = chat_history_df[chat_history_df["Title"] == selected_chat].iloc[0]

        # 🔹 Wrap messages inside a container for scrollability
        st.subheader("Chat Messages:")
        with st.container(height=600):

            for message in chat_row["Messages"]:
                role = message["role"]
                content = message["content"]
                icon = icons.get(role, "")

                with st.chat_message(role, avatar=icon):
                    # Convert DataFrame objects back into readable DataFrames
                    if isinstance(content, pd.DataFrame):
                        st.dataframe(content, hide_index=True, use_container_width=True)
                    else:
                        try:
                            # If content is a JSON-encoded string, try converting it into a DataFrame
                            content_json = json.loads(content)
                            if isinstance(content_json, list) and all(isinstance(i, dict) for i in content_json):
                                content_df = pd.DataFrame(content_json)
                                st.dataframe(content_df, hide_index=True, use_container_width=True)
                            else:
                                st.markdown(f"**{role.capitalize()}:** {content}")  # Normal text
                        except json.JSONDecodeError:
                            st.markdown(f"**{role.capitalize()}:** {content}")  # Normal text

    # Allow continuing chat
    if st.button("Continue Chat", use_container_width=True, type="primary"):
        st.session_state.chat_id = chat_row["Chat ID"]
        st.session_state.general_messages = chat_row["Messages"]
        st.session_state.general_chat_history = chat_row["Chat Summary"]
        st.success("Chat loaded successfully! Redirecting...")
        st.switch_page("pages/Prospect_Finder.py")  # Adjust path as needed
