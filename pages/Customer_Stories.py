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

st.title("📚 Customer Story Manager")
st.markdown("---")

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

st.markdown("### Add a New Customer Story")
cols = st.columns(2)
with cols[0]:
    customer_name = st.text_input("Customer Company Name", key="company_name", placeholder="Type here...")
with cols[1]:
    customer_industry = st.text_input("Customer Industry", key="company_industry", placeholder="Type here...")

customer_story = st.text_area("Customer Success Story", height=200, key="customer_story", placeholder="Type here...")

if st.button("Save Customer Story", use_container_width=True, type='primary'):
    if not customer_name.strip():
        st.warning("Please enter the company name for the customer before saving.")
    elif not customer_industry.strip():
        st.warning("Please enter the industry of the customer before saving.")
    elif not customer_story.strip():
        st.warning("Please enter a success story before saving.")
    else:
        story_id = str(uuid.uuid4())
        escaped_customer_name = customer_name.replace("'", "''")
        escaped_customer_story = customer_story.replace("'", "''")
        escaped_customer_industry = customer_industry.replace("'", "''")

        insert_query = f"""
            INSERT INTO STORIES (INDUSTRY, TEXT, USERNAME, DATE_ADDED, COMPANY_NAME, STORY_ID)
            VALUES ('{escaped_customer_industry}', '{escaped_customer_name} - {escaped_customer_story}', '{username}', '{datetime.now()}', '{escaped_customer_name}', '{story_id}')
        """
        with st.spinner(text="In progress..."):
            try:
                session.sql(insert_query).collect()
                st.toast(f"Customer Story for '{escaped_customer_name}' added!", icon="🎉")

                cortex_search_query = """
                    CREATE OR REPLACE CORTEX SEARCH SERVICE LINKEDIN.public.stories
                    ON text
                    ATTRIBUTES company_name, industry
                    WAREHOUSE = compute_wh
                    TARGET_LAG = '24 hours'
                    EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
                    AS (
                        SELECT 
                            text,
                            industry,
                            company_name
                        FROM LINKEDIN.public.stories
                    );
                """
                session.sql(cortex_search_query).collect()
                st.toast("Cortex Search function successfully updated!", icon="✅")
                
            except Exception as e:
                st.error(f"Error saving template: {e}")


st.markdown("---")

# 📌 Section: Manage Your Customer Stories
st.markdown("### Manage Your Customer Stories")

# Fetch only the stories that belong to the logged-in user
query = f"SELECT STORY_ID, COMPANY_NAME, INDUSTRY, TEXT, DATE_ADDED FROM STORIES WHERE USERNAME = '{username}' ORDER BY DATE_ADDED"
user_stories = session.sql(query).collect()

if not user_stories:
    st.info("You have no customer stories yet.")
else:
    with st.container(height=350):  
        for story in user_stories:
            story_id = story["STORY_ID"]
            company_name = story["COMPANY_NAME"]
            industry = story["INDUSTRY"]
            story_text = story["TEXT"].replace(f"{company_name} - ", "", 1)  # Remove company name prefix
            date_added = story["DATE_ADDED"]

            with st.expander(f"📖 {company_name} - {industry} ({date_added})"):
                updated_name = st.text_input("Company Name", company_name, key=f"name_{story_id}")
                updated_industry = st.text_input("Industry", industry, key=f"industry_{story_id}")
                updated_story = st.text_area("Success Story", story_text, height=150, key=f"story_{story_id}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update", key=f"update_{story_id}", use_container_width=True):
                        update_query = """
                            UPDATE STORIES 
                            SET COMPANY_NAME = ?, 
                                INDUSTRY = ?, 
                                TEXT = ?
                            WHERE STORY_ID = ?
                        """
                        updated_text = f"{updated_name} - {updated_story}"

                        with st.spinner(text="Updating story..."):
                            try:
                                session.sql(update_query, params=[updated_name, updated_industry, updated_text, story_id]).collect()
                                st.toast(f"Updated story for '{updated_name}'!", icon="🎉")

                                # Re-run Cortex Search function to update search index
                                cortex_search_query = """
                                    CREATE OR REPLACE CORTEX SEARCH SERVICE LINKEDIN.public.stories
                                    ON text
                                    ATTRIBUTES company_name, industry
                                    WAREHOUSE = compute_wh
                                    TARGET_LAG = '24 hours'
                                    EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
                                    AS (
                                        SELECT 
                                            text,
                                            industry,
                                            company_name
                                        FROM LINKEDIN.public.stories
                                    );
                                """
                                session.sql(cortex_search_query).collect()
                                st.toast("Cortex Search function successfully updated!", icon="✅")

                            except Exception as e:
                                st.error(f"Error updating story: {e}")

                with col2:
                    if st.button("Delete", key=f"delete_{story_id}", use_container_width=True):
                        delete_query = "DELETE FROM STORIES WHERE STORY_ID = ?"
                        with st.spinner(text="Deleting story..."):
                            try:
                                session.sql(delete_query, params=[story_id]).collect()
                                st.toast(f"Deleted story.", icon="🎉")

                                # Re-run Cortex Search function to update search index
                                cortex_search_query = """
                                    CREATE OR REPLACE CORTEX SEARCH SERVICE LINKEDIN.public.stories
                                    ON text
                                    ATTRIBUTES company_name, industry
                                    WAREHOUSE = compute_wh
                                    TARGET_LAG = '24 hours'
                                    EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
                                    AS (
                                        SELECT 
                                            text,
                                            industry,
                                            company_name
                                        FROM LINKEDIN.public.stories
                                    );
                                """
                                session.sql(cortex_search_query).collect()
                                st.toast("Cortex Search function successfully updated!", icon="✅")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting story: {e}")


# 📌 Section: Navigation Buttons
if st.button("Go to Message Generation", use_container_width=True):
    st.switch_page("pages/Message_Generation.py")