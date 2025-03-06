import streamlit as st
import uuid
import os
from functions.helper_global import *
from datetime import datetime
import fitz

UNWANTED_PHRASES = [
    "View Full Case Study",
    "EXTERNALLY REFERENCEABLE",
    "View Full Video Here",
]

def clean_text(text):
    # Remove specific phrases
    for phrase in UNWANTED_PHRASES:
        text = text.replace(phrase, "")
    
    # Remove © {any year} Snowflake Inc. All Rights Reserved
    text = re.sub(r"©\s\d{4}\sSnowflake Inc\. All Rights Reserved", "", text)
    
    return text.strip()

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

check_duplicate_story = "SELECT COUNT(*) AS count FROM stories WHERE text = ?"
def is_duplicate(story):
    result = session.sql(check_duplicate_story, params=[story]).collect()
    return result[0]["COUNT"] > 0

st.title("📚 Customer Story Manager")
st.markdown("---")

if st.session_state.logged_in and st.session_state.username == 'admin': 
    session = create_session()

    username = st.session_state["username"]

    adding_customer_story = f"""INSERT INTO STORIES(TEXT, USERNAME, DATE_ADDED, STORY_ID, INDUSTRY) VALUES(?, ?, ?, ?, ?)"""

    st.markdown("### Add a New Customer Story")
    columns = st.columns(2)
    with columns[0]:
        file = st.file_uploader(label="Upload your customer stories", type="pdf", key="customer_story_pdf")
    with columns[1]:
        industry = st.text_input(label="Industry", placeholder="Enter the Industry...", key="customer_industry", )

    if file:
        file.seek(0)
        with st.container(height=600):
            pdf_bytes = file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            full_text = ""
            combined_text = ""
            all_stories = []

            for page_number, page in enumerate(doc, start=1):
                page_text = page.get_text()
                cleaned_text = clean_text(page_text)
                combined_text += cleaned_text + "\n\n"
                

                # Every 2 pages or at the end of the document
                if page_number % 2 == 0 or page_number == len(doc):
                    story = combined_text.strip()
                    all_stories.append(story)

                    with st.container(height=300):
                        st.write(story)
                    if st.button(
                        "Add Customer Story",
                        use_container_width=True,
                        key=f"add_story_{page_number}"
                    ):
                        try:
                            if is_duplicate(story):
                                st.toast("Duplicate story found. Skipping.", icon="❌")
                            else:
                                id = uuid.uuid4()
                                session.sql(adding_customer_story, params=[story, st.session_state.username, datetime.now(), str(id), st.session_state.customer_industry]).collect()
                                st.toast("Added Customer Story.", icon="🎉")
                        except Exception as e:
                            st.error(f"Error adding story: {e}")


                    combined_text = ""

                    full_text += combined_text + "\n\n"
                    combined_text = ""
        if all_stories:
            if st.button("Upload All Customer Stories", use_container_width=True, type="primary"):
                duplicates = 0
                uploaded = 0
                try:
                    for i, story in enumerate(all_stories, start=1):
                        if is_duplicate(story):
                            st.toast(f"Story {i} is a duplicate. Skipping.", icon="❌")
                            duplicates += 1
                        else:
                            id = uuid.uuid4()
                            session.sql(adding_customer_story, params=[story, st.session_state.username, datetime.now(), str(id), st.session_state.customer_industry]).collect()
                            st.toast(f"Uploaded story {i}", icon="✅")
                            uploaded += 1
                    st.success(f"{uploaded} new stories uploaded. {duplicates} duplicates skipped.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error uploading stories: {e}")


    st.markdown("---")

    # 📌 Section: Manage Your Customer Stories
    st.markdown("### Manage Your Customer Stories")

    query = f"""
        SELECT * FROM STORIES 
        WHERE USERNAME = ? ORDER BY DATE_ADDED
    """
    stories = session.sql(query, params=[username]).collect()


    if not stories:
        st.info("You have no customer stories yet.")
    else:
        # Search bar
        st.text_input("Search Customer Stories", key='story_search', placeholder="Type to search...").strip().lower()

        filtered_stories = [story for story in stories if st.session_state.story_search in story["TEXT"].lower()]

        if st.session_state.story_search and not filtered_stories:
            st.warning("No customer stories found.")
            if st.button("Reset Search", key="reset_story_search", use_container_width=True):
                if st.session_state.story_search:
                    del st.session_state.story_search
                    st.session_state.story_search = ''
                st.rerun()

        if filtered_stories:
            with st.container(height=350):  
                for number, story in enumerate(filtered_stories, start=1):
                    story_id = story["STORY_ID"]
                    date_added = story["DATE_ADDED"]
                    industry = story["INDUSTRY"]
                    text = story["TEXT"]

                    with st.expander(f"Story {number} - {industry}"):
                        updated_instry = st.text_input("Industry", industry, key=f"industry_{story_id}")
                        updated_story = st.text_area("Success Story", text, height=150, key=f"story_{story_id}")

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Update", key=f"update_{story_id}", use_container_width=True):
                                update_query = """
                                    UPDATE STORIES 
                                    SET TEXT = ?
                                    WHERE STORY_ID = ?
                                """
                                # with st.spinner(text="Updating story...",  show_time=True):
                                #     try:
                                #         session.sql(update_query, params=[updated_story, story_id]).collect()
                                #         st.toast(f"Updated story for!", icon="🎉")

                                #         # Re-run Cortex Search function to update search index
                                #         cortex_search_query = """
                                #             CREATE OR REPLACE CORTEX SEARCH SERVICE LINKEDIN.public.stories
                                #             ON text
                                #             ATTRIBUTES industry
                                #             WAREHOUSE = compute_wh
                                #             TARGET_LAG = '24 hours'
                                #             EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
                                #             AS (
                                #                 SELECT 
                                #                     text
                                #                 FROM LINKEDIN.public.stories
                                #             );
                                #         """
                                #         session.sql(cortex_search_query).collect()
                                #         st.toast("Cortex Search function successfully updated!", icon="✅")

                                #     except Exception as e:
                                #         st.error(f"Error updating story: {e}")

                        with col2:
                            if st.button("Delete", key=f"delete_{story_id}", use_container_width=True):
                                delete_query = "DELETE FROM STORIES WHERE STORY_ID = ?"
                                session.sql(delete_query, params=[story_id]).collect()
                                st.toast(f"Deleted story.", icon="🎉")
                                # with st.spinner(text="Deleting story...",  show_time=True):
                                #     try:
                                #         session.sql(delete_query, params=[story_id]).collect()
                                #         st.toast(f"Deleted story.", icon="🎉")

                                #         # Re-run Cortex Search function to update search index
                                #         cortex_search_query = """
                                #             CREATE OR REPLACE CORTEX SEARCH SERVICE LINKEDIN.public.stories
                                #             ON text
                                #             ATTRIBUTES industry
                                #             WAREHOUSE = compute_wh
                                #             TARGET_LAG = '24 hours'
                                #             EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
                                #             AS (
                                #                 SELECT 
                                #                     text
                                #                 FROM LINKEDIN.public.stories
                                #             );
                                #         """
                                #         session.sql(cortex_search_query).collect()
                                #         st.toast("Cortex Search function successfully updated!", icon="✅")
                                #         st.rerun()
                                #     except Exception as e:
                                #         st.error(f"Error deleting story: {e}")
else:
    st.info("Only administrators can manage customer success stories.")

# 📌 Section: Navigation Buttons
if st.button("Go to Message Generation", use_container_width=True):
    st.switch_page("pages/Message_Generation.py")