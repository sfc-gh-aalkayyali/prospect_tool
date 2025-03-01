import streamlit as st
import uuid
import os
from functions.helper_global import *
from datetime import datetime

init_session_state()
if "battlecard_search" not in st.session_state:
    st.session_state.battlecard_search = ""

cols = st.columns([85, 15])
with cols[1]:
    if st.session_state.username != "guest":
        if st.button("Logout", use_container_width=True):
            logout()
    else:
        if st.button("Login", use_container_width=True):
            st.session_state.login_show_confirm = True

with cols[0]:
    if st.session_state.login_show_confirm:
        st.warning("⚠ You will be redirected to the homepage to login or register and you will lose all chat history. ⚠")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅", use_container_width=True):
                logout()
        with col2:
            if st.button("❌", use_container_width=True):
                st.session_state.login_show_confirm = False
                st.rerun()

st.title("🛡️ Battlecards Manager")
st.markdown("---")

session = create_session()

if "logged_in" not in st.session_state or not st.session_state["logged_in"] or st.session_state["username"] == "guest":
    st.warning("Please log in or register to manage battlecards.")
    if st.button("Login or Register", use_container_width=True):
        st.session_state["battlecards_manager_show_confirm"] = True
    
    if st.session_state.battlecards_manager_show_confirm:
        st.error("⚠ If you continue, this will take you to the homepage to login or register and you will lose all chat history. Do you want to continue? ⚠")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Continue", use_container_width=True):
                st.session_state.clear()
                st.rerun()
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.battlecards_manager_show_confirm = False
                st.rerun()
    st.stop()

username = st.session_state["username"]

st.markdown("### Create a New Battlecard")

cols2 = st.columns(2)
with cols2[0]:
    battlecard_name = st.text_input("Comeptitor Company Name", placeholder="e.g., Databricks, Redshift...")

with cols2[1]:
    battlecard_industry = st.text_input("Comeptitor Company Industry", placeholder="e.g., Telecommunications...")
  
cols = st.columns(2)
with cols[0]:
    battlecard_strengths = st.text_area("Strengths", height=100, placeholder="List the key strengths...")

with cols[1]:
    battlecard_weaknesses = st.text_area("Weaknesses", height=100, placeholder="List the weaknesses...")

battlecard_snowflake_response = st.text_area("Snowflake Response", height=100, placeholder="How does Snowflake compare?")

submitted = st.button("Save Battlecard", use_container_width=True, type='primary')

if submitted:
    if not battlecard_name.strip() or not battlecard_industry.strip():
        st.warning("Please enter the name and industry of the battlecard before saving.")
    elif not battlecard_strengths.strip() or not battlecard_weaknesses.strip() or not battlecard_snowflake_response.strip():
        st.warning("Please complete all fields before saving.")
    else:
        battlecard_id = str(uuid.uuid4())
        
        battlecard_text = f"""
Competitor Name: {battlecard_name}
\nIndustry: {battlecard_industry}
\nStrengths:\n{battlecard_strengths}
\nWeaknesses:\n{battlecard_weaknesses}
\nSnowflake Response:\n{battlecard_snowflake_response}
        """.strip()

        insert_query = """
            INSERT INTO BATTLECARDS (INDUSTRY, TEXT, USERNAME, DATE_ADDED, COMPANY_NAME, BATTLE_CARD_ID)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        try:
            session.sql(insert_query, params=[
            battlecard_industry, 
            battlecard_text, 
            username, 
            datetime.now(), 
            battlecard_name,
            battlecard_id
            ]).collect()
            st.toast(f"Added Battle Card for {battlecard_name}.", icon="🎉")
            
            cortex_search_query = """
                CREATE OR REPLACE CORTEX SEARCH SERVICE LINKEDIN.public.battlecard
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
                    FROM LINKEDIN.public.battlecards
                );
            """
            session.sql(cortex_search_query).collect()
            st.toast("Cortex Search function successfully updated!", icon="✅")
            
        except Exception as e:
            st.error(f"Error saving template: {e}")

st.markdown("---")

st.markdown("### Manage Your Battlecards")

query = f"""
    SELECT * FROM BATTLECARDS 
    WHERE USERNAME = ? ORDER BY DATE_ADDED
"""
battlecards = session.sql(query, params=[username]).collect()

if not battlecards:
    st.info("You have no battlecards yet.")
else:
    st.text_input("Search Battlecards", key='battlecard_search', placeholder="Type to search...").strip().lower()
    
    filtered_battlecards = [bc for bc in battlecards if st.session_state.battlecard_search in bc["COMPANY_NAME"].lower()]
    
    if st.session_state.battlecard_search and not filtered_battlecards:
        st.warning("No battlecards found.")
        if st.button("Reset Search", key="reset_battlecard_search", use_container_width=True):
            if st.session_state.battlecard_search:
             del st.session_state.battlecard_search
             st.session_state.battlecard_search = ''
            st.rerun()
    
    if filtered_battlecards:
        with st.container(height=350):  
            for bc in filtered_battlecards:
                battlecard_id = bc["BATTLE_CARD_ID"]
                name = bc["COMPANY_NAME"]
                text = bc["TEXT"]
                
                with st.expander(f"{name}"):
                    updated_name = st.text_input("Battlecard Name", name, key=f"name_{battlecard_id}")
                    updated_info = st.text_area("Information", text, key=f"strengths_{battlecard_id}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Update", key=f"update_{battlecard_id}", use_container_width=True):
                            update_query = """
                                UPDATE BATTLECARDS 
                                SET COMPANY_NAME = ?, 
                                    TEXT = ?
                                WHERE BATTLE_CARD_ID = ?
                            """
                            with st.spinner(text="Updating battlecard...", show_time=True):
                                try:
                                    session.sql(update_query, params=[updated_name, updated_info, battlecard_id]).collect()
                                    st.toast(f"Updated Battle Card for {updated_name}.", icon="🎉")
                                    
                                    # Re-run Cortex Search function to update search index
                                    cortex_search_query = """
                                        CREATE OR REPLACE CORTEX SEARCH SERVICE LINKEDIN.public.battlecard
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
                                            FROM LINKEDIN.public.battlecards
                                        );
                                    """
                                    session.sql(cortex_search_query).collect()
                                    st.toast("Cortex Search function successfully updated!", icon="✅")

                                except Exception as e:
                                    st.error(f"Error updating battlecard: {e}")




                    with col2:
                        if st.button("Delete", key=f"delete_{battlecard_id}", use_container_width=True):
                            delete_query = "DELETE FROM BATTLECARDS WHERE BATTLE_CARD_ID = ?"
                            with st.spinner(text="Deleting battlecard...",  show_time=True):
                                try:
                                    session.sql(delete_query, params=[battlecard_id]).collect()
                                    st.toast(f"Deleted Battle Card.", icon="🎉")

                                    # Re-run Cortex Search function to update search index
                                    cortex_search_query = """
                                        CREATE OR REPLACE CORTEX SEARCH SERVICE LINKEDIN.public.battlecard
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
                                            FROM LINKEDIN.public.battlecards
                                        );
                                    """
                                    session.sql(cortex_search_query).collect()
                                    st.toast("Cortex Search function successfully updated!", icon="✅")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting battlecard: {e}")


# 📌 Section: Navigation Buttons
if st.button("Go to Message Generation", use_container_width=True):
    st.switch_page("pages/Message_Generation.py")