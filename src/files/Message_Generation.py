from functions.helper_global import *
from functions.helper_generation import *
from functions.helper_session import *
import pandas as pd
from datetime import datetime
import streamlit as st
import uuid
import os

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

username = st.session_state.username

# num_templates = """
#     SELECT COUNT(*) FROM TEMPLATES 
#     WHERE USERNAME = ?
# """
# number_of_templates = session.sql(num_templates, params=[username]).collect()[0][0]

# if existing_template_count > 0:

# Fetch user templates from Snowflake

## Check if user logged in
user_templates = session.sql(f"""
    SELECT ID, NAME_OF_TEMPLATE, USER_PROMPT, MESSAGE_TEXT
    FROM TEMPLATES 
    WHERE USERNAME = '{username}'
    ORDER BY DATE_ADDED
""").to_pandas()


st.title(":speech_balloon: Message Generation")
st.markdown("---")
st.session_state.temperature = 0.7
st.session_state.top_p = 0.9

if user_templates.shape[0] == 0 and username != 'guest':
    st.warning("Please create message templates before using this feature.")
    if st.button("Go to Template Manager", use_container_width=True):
        st.switch_page("files/Template_Manager.py")
elif user_templates.shape[0] == 0 and username == 'guest':
    st.warning("This feature is currently unavailable for guests, please login or Signup to continue.")
else:
    # Ensure there are available templates
    template_options = user_templates["NAME_OF_TEMPLATE"].tolist() if not user_templates.empty else []

    if "message_type" not in st.session_state or st.session_state.message_type not in template_options:
        st.session_state.message_type = template_options[0] if template_options else None


    people_df = st.session_state.general_profiles

    if not people_df.empty:  
        init_service_metadata()
        session = create_session()
        username = st.session_state["username"]
        init_config_options_generation()

        if st.sidebar.button("Clear Selections", use_container_width=True, type="secondary"):
            del st.session_state.service_metadata
            del st.session_state.generated_messages
            del st.session_state.uploaded_messages
            del st.session_state.customer_stories_docs
            del st.session_state.selected_customer_stories_docs
            st.session_state.customer_stories_docs = []
            st.session_state.uploaded_messages = ""
            st.session_state.selected_customer_stories_docs = []

            if st.session_state.profile_selection:
                del st.session_state.profile_selection
                st.session_state.profile_selection = []

            if st.session_state.customer_stories_industry:
                del st.session_state.customer_stories_industry
                st.session_state.customer_stories_industry = []

            if st.session_state.message_type:
                del st.session_state.message_type
                st.session_state.message_type = template_options[0]


            st.rerun()
        
        st.markdown("### Profile Selection")
        people_df = people_df.drop_duplicates(subset=['Full Name'])

        selected_names = st.multiselect("Select Profiles:", people_df['Full Name'].tolist(), default=st.session_state.profile_selection)

        selected_profiles_df = people_df[people_df['Full Name'].isin(selected_names)]

        
        if not selected_profiles_df.empty and ("LinkedIn" in selected_profiles_df.columns or "LinkedIn URL" in selected_profiles_df.columns):
            linkedin_col = "LinkedIn" if "LinkedIn" in selected_profiles_df.columns else "LinkedIn URL"
            linkedin_urls = selected_profiles_df[linkedin_col].dropna().unique().tolist()

            if linkedin_urls:
                contact_query = f"""
                    SELECT linkedin_url, contacted_by, contacted_on
                    FROM LINKEDIN.PUBLIC.PROSPECT_TOUCH_LOG
                    WHERE linkedin_url IN ({','.join(['?'] * len(linkedin_urls))})
                    ORDER BY contacted_on DESC
                """
                logs_df = session.sql(contact_query, params=linkedin_urls).to_pandas()
                logs_df.columns = [col.lower() for col in logs_df.columns]  # normalize to lowercase

                if not logs_df.empty:
                    contact_log_map = logs_df.groupby("linkedin_url").first().to_dict(orient="index")

                    def get_contact_status(url):
                        info = contact_log_map.get(url)
                        if info:
                            return f"⚠️ Contacted by {info['contacted_by']} on {pd.to_datetime(info['contacted_on']).strftime('%b %d')}"
                        return "Not contacted"

                    selected_profiles_df["Contact Status"] = selected_profiles_df[linkedin_col].apply(get_contact_status)
                else:
                    selected_profiles_df["Contact Status"] = "Not contacted"
            else:
                selected_profiles_df["Contact Status"] = "❓ No LinkedIn URL"

       
        if not selected_profiles_df.empty:
            with st.container(height=300):
                for index, row in selected_profiles_df.iterrows():
                    contact_status = row.get("Contact Status", "❓ Unknown")

                    st.markdown(f"**👤 {row['Full Name']}**")
                    st.markdown(f"""🔍 <span style="color: red;">{contact_status}</span>""", unsafe_allow_html=True)

                    profile_details = "\n".join([
                        f"{col}: {val}" for col, val in row.items()
                        if col not in ["Full Name", "Contact Status"]
                    ])

                    st.text_area(label="", value=profile_details, height=200)




            st.markdown("---")
            st.markdown("### Customer Success Stories (OPTIONAL)")
            col1, col2 = st.columns([0.6, 0.4])

            with col1:
                st.text_input("Search Keyword", placeholder="Enter keyword...", key="customer_stories_search")
            with col2:
                industries = session.sql('SELECT DISTINCT INDUSTRY FROM LINKEDIN.PUBLIC."STORIES"').to_pandas()
                industries = industries.dropna().loc[industries['INDUSTRY'].astype(str).str.strip() != '']
                selected_industries = st.multiselect("Select Industry (OPTIONAL)", industries,  default=st.session_state.customer_stories_industry)
                st.session_state.customer_stories_industry = selected_industries
            st.slider("Limit stories retrieved", min_value=1, max_value=20, value=3, key="customer_stories_limit")
            
            def find_stories():
                if st.session_state.customer_stories_docs and st.session_state.customer_stories_docs != []:
                    del st.session_state.customer_stories_docs
                    st.session_state.customer_stories_docs = []
                    
                if st.session_state.customer_stories_search and st.session_state.customer_stories_search.strip() != '':
                    results, search_column = query_stories_cortex_search_service(
                        st.session_state.customer_stories_search
                    )
                    st.session_state.customer_stories_docs = [r[search_column] for r in results]
                else:
                    st.warning("You must enter a keyword search")

            if st.button("Find Customer Stories", use_container_width=True):
                find_stories()

            if st.session_state.customer_stories_docs != []:
                formatted_stories = [p.replace("\n", "<br>") for p in st.session_state.customer_stories_docs]
                st.write("Customer Stories")
                with st.container(height=300):
                    for i, story in enumerate(formatted_stories, start=1):
                        with st.container(height=200):
                            selected = st.checkbox(f"Select Customer Story {i}", key=f"story_key{i}")
                            st.markdown(f"{story}", unsafe_allow_html=True)
                        if selected and story not in st.session_state.selected_customer_stories_docs:
                            st.session_state.selected_customer_stories_docs.append(story)
                        elif not selected and story in st.session_state.selected_customer_stories_docs:
                            st.session_state.selected_customer_stories_docs.remove(story)

            ### Add Battle Cards here

            st.markdown("---")
            st.markdown("### Competitive Battlecards (OPTIONAL)")

            col1, col2 = st.columns([0.6, 0.4])

            with col1:
                st.text_input("Search Keyword", placeholder="Enter keyword...", key="battle_cards_search")
                st.slider("Limit battle cards retrieved", min_value=1, max_value=20, value=3, key="battle_card_limit")
            with col2:
                battle_cards_industries = session.sql('SELECT DISTINCT INDUSTRY FROM LINKEDIN.PUBLIC."BATTLECARDS"').to_pandas()
                battle_cards_industries = battle_cards_industries.dropna().loc[battle_cards_industries['INDUSTRY'].astype(str).str.strip() != '']
                selected_battle_card_industries = st.multiselect("Select Industry (OPTIONAL)", battle_cards_industries,  default=st.session_state.battle_card_industry)
                st.session_state.battle_card_industry = selected_battle_card_industries

                battle_cardcompanies = session.sql('SELECT DISTINCT COMPANY_NAME FROM LINKEDIN.PUBLIC."BATTLECARDS"').to_pandas()
                battle_cardcompanies = battle_cardcompanies.dropna().loc[battle_cardcompanies['COMPANY_NAME'].astype(str).str.strip() != '']
                selected_battle_card_companies = st.multiselect("Select Company (OPTIONAL)", battle_cardcompanies, default=st.session_state.battle_card_company)
                st.session_state.battle_card_company = selected_battle_card_companies

            
            def find_battle_cards():
                if st.session_state.customer_battle_cards and st.session_state.customer_battle_cards != []:
                    del st.session_state.customer_battle_cards
                    st.session_state.customer_battle_cards = []

                if st.session_state.battle_cards_search and st.session_state.battle_cards_search.strip() != '':
                    results, search_column = query_battle_cards_cortex_search_service(
                        st.session_state.battle_cards_search
                    )
                    st.session_state.customer_battle_cards = [r[search_column] for r in results]
                else:
                    st.warning("You must enter a keyword search")

            if st.button("Find Battle Cards", use_container_width=True):
                find_battle_cards()

            if st.session_state.customer_battle_cards != []:
                formatted_battle_cards = [p.replace("\n", "<br>") for p in st.session_state.customer_battle_cards]
                st.write("Battle Cards")
                with st.container(height=300):
                    for i, battle_card in enumerate(formatted_battle_cards, start=1):
                        with st.container(height=200):
                            selected = st.checkbox(f"Select Battle Card {i}", key=f"battle_card{i}")
                            st.markdown(f"{battle_card}", unsafe_allow_html=True)
                        if selected and battle_card not in st.session_state.selected_battle_cards:
                            st.session_state.selected_battle_cards.append(battle_card)
                        elif not selected and battle_card in st.session_state.selected_battle_cards:
                            st.session_state.selected_battle_cards.remove(battle_card)
            query = f"""
                    SELECT * FROM CUSTOMER_DOCUMENTS 
                    WHERE USERNAME = ? ORDER BY DATE
                """

            documents = session.sql(query, params=[username]).collect()

            if not documents:
               pass
            else:
                # Search bar
                st.markdown("---")
                st.subheader("Prospect Documents (OPTIONAL)")
                st.text_input("Search Prospect Documents", key='document_search2', placeholder="Type to search...").strip().lower()

                filtered_documents = [story for story in documents if st.session_state.document_search2 in story["CONTENT"].lower()]

                if st.session_state.document_search2 and not filtered_documents:
                    st.warning("No prospect documents found.")
                    if st.button("Reset Search", key="reset_document_search2", use_container_width=True):
                        if st.session_state.document_search2:
                            del st.session_state.document_search2
                            st.session_state.document_search2 = ''
                        st.rerun()

                if filtered_documents:
                    with st.container(height=300):  
                        for number, story in enumerate(filtered_documents, start=1):
                            with st.container(height=200):
                                selected_document = st.checkbox(f"Select Document {number}", key=f"prospect_document_{number}")
                                story_id = story["ID"]
                                date_added = story["DATE"]
                                title = story["TITLE"]
                                customer = story["CUSTOMER"]
                                text = story["CONTENT"]
                                updated_name = st.text_input("Prospect Name", customer, key=f"industry2_{story_id}")
                                updated_title = st.text_input("Prospect Title", title, key=f"title2_{story_id}")
                                updated_text = st.text_area("Prospect Document", text, height=150, key=f"story2_{story_id}")

                                current_doc = {
                                    "id": story_id,
                                    "customer": updated_name,
                                    "title": updated_title,
                                    "text": updated_text
                                }

                                already_selected = any(doc["id"] == story_id for doc in st.session_state.selected_document)

                                if selected_document and not already_selected:
                                    st.session_state.selected_document.append(current_doc)
                                elif not selected_document and already_selected:
                                    st.session_state.selected_document = [
                                        doc for doc in st.session_state.selected_document if doc["id"] != story_id
                                    ]
            st.markdown("---")
            st.markdown("### Customize & Save Template")

            if template_options:
                message_type = st.selectbox(
                    "Select from Available Templates",
                    template_options,
                    index=template_options.index(st.session_state.message_type) if st.session_state.message_type in template_options else 0
                )

                # Retrieve selected template details
                selected_template_data = user_templates[user_templates["NAME_OF_TEMPLATE"] == message_type]

                system_prompt = selected_template_data["USER_PROMPT"].values[0] if not selected_template_data.empty else ""
                message_text = selected_template_data["MESSAGE_TEXT"].values[0] if not selected_template_data.empty else ""

                # Editable text areas for prompt and message
                col1, col2 = st.columns([0.5, 0.5])
                with col1:
                    system_prompt = st.text_area(
                        "Customize Prompt",
                        value=system_prompt,
                        height=250,
                        placeholder="Type here..."
                    )
                    st.session_state.system_prompt = system_prompt

                with col2:
                    message_text = st.text_area(
                        "Customize Message",
                        value=message_text,
                        height=250,
                        placeholder="Type here...",
                    )
                    st.session_state.sample_message = message_text

                if st.session_state["logged_in"] and username != "guest":
                    if st.button("Update Template", use_container_width=True):
                        if st.session_state.message_type.strip() == '' or st.session_state.message_type is None:
                            st.warning("Please choose a template to save.")
                        elif not system_prompt.strip() or not message_text.strip():
                            st.warning("Please enter both a prompt and message before saving.")
                        else:
                            check_query = """
                                SELECT COUNT(*) FROM TEMPLATES 
                                WHERE NAME_OF_TEMPLATE = ? AND USERNAME = ?
                            """
                            existing_template_count = session.sql(check_query, params=[st.session_state.message_type, username]).collect()[0][0]

                            if existing_template_count > 0:
                                # Update existing template
                                update_query = """
                                    UPDATE TEMPLATES 
                                    SET USER_PROMPT = ?, 
                                        MESSAGE_TEXT = ?, 
                                        DATE_ADDED = CURRENT_TIMESTAMP
                                    WHERE NAME_OF_TEMPLATE = ? AND USERNAME = ?
                                """
                                try:
                                    session.sql(update_query, params=[system_prompt, message_text, st.session_state.message_type, username]).collect()
                                    st.success(f"Template '{st.session_state.message_type}' updated successfully!")
                                except Exception as e:
                                    st.error(f"Error updating template: {e}")

                            else:
                                st.warning("Template not found, please create one first.")

                            st.rerun()

                else:
                    if st.button("Log in or create an account to save templates.", use_container_width=True):
                        st.session_state["message_generation_show_confirm"] = True

                    if st.session_state.message_generation_show_confirm:
                        st.error("⚠ If you continue, this will take you to the homepage to login or register and you will lose all chat history. Do you want to continue? ⚠")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Continue", use_container_width=True):
                                st.session_state.clear()
                                st.rerun()
                        with col2:
                            if st.button("❌ Cancel", use_container_width=True):
                                st.session_state.message_generation_show_confirm = False
                                st.rerun()
            else:
                st.warning("No templates available. Please create one in the template manager.")

            token_counter = f"""SELECT SNOWFLAKE.CORTEX.COUNT_TOKENS(?, ?) as token_count;"""

            ### set token limitation to 5% less than actual for a margin of error
            token_count_limitation = {
                "deepseek-r1": 31130,
                "llama3.1-70b": 121600
            }

            if st.button("Generate Messages", type="primary", use_container_width=True):
                if st.session_state.system_prompt and st.session_state.sample_message and st.session_state.system_prompt.strip() != '' and st.session_state.sample_message.strip() != '':
                    with st.spinner("Generating messages...",  show_time=True):
                        try:
                            generated_messages = {}
                            for _, row in selected_profiles_df.iterrows():
                                message = create_direct_message(row.to_dict())
                                token_count = session.sql(token_counter, params=[st.session_state.selected_model, str(message)]).collect()
                                if token_count:
                                    token_count = token_count[0]["TOKEN_COUNT"]
                                    if token_count <= token_count_limitation[st.session_state.selected_model]:
                                        generated_messages[row['Full Name']] = complete_function(message)
                                    else:
                                        st.error(f"""You have exceeded the input token limitation for the {st.session_state.selected_model} model.\n
This model has an input limitation of roughly {token_count_limitation[st.session_state.selected_model]} tokens which is equivalent to about {round(token_count_limitation[st.session_state.selected_model]/4, 0):.0f} words.\n
Current Model: {st.session_state.selected_model}\n
Total Token Usage: {token_count} tokens\n
Used {token_count} tokens out of {token_count_limitation[st.session_state.selected_model]} which is about {round((token_count / token_count_limitation[st.session_state.selected_model]) * 100, 0):.0f}% usage.""".strip())
                                        st.info(f"""*If you are using the deepseek-r1 model and you are running into input token limitations please consider switching to llama3.1-70b as it has 4x more input token capacity.*\n
*If you are still running into input token limitations after switching to the llama model, please consider removing or shortening customer documents, stories, battlecards.*""")
                            st.session_state.generated_messages = generated_messages
                        except Exception as e:
                            st.error(e)
                else:
                    st.warning("Please input a prompt and sample message to generate messages.")

            if st.session_state.get("generated_messages"):
                st.markdown("---")
                st.markdown("#### Generated Messages")
                all_messages = ""
                with st.container(height=300): 
                    for name, message in st.session_state.generated_messages.items():
                        col1, col2 = st.columns([0.9, 0.1])
                        with col1:
                            st.text_area(f"{name}:", value=message, height=300, placeholder="Type here...")
                        with col2:
                            st.download_button("📥", data=message, file_name=f"{name.replace(' ', '_')}_message.txt", mime="text/plain", key=f"download_{name}")

                        all_messages += f"---\n{name}:\n{message}\n\n"

                if all_messages:
                    st.download_button("Download All Messages", data=all_messages, file_name="all_generated_messages.txt", mime="text/plain", use_container_width=True, key="download_all")


    

                # Add "Log Outreach" section
                st.markdown("---")
                st.markdown("### Log Outreach")

                # Ensure outreach_notes is a dictionary
                if "outreach_notes" not in st.session_state or not isinstance(st.session_state.outreach_notes, dict):
                    st.session_state.outreach_notes = {}

                with st.expander("Add notes for each profile before logging (optional)", expanded=True):
                    for _, row in selected_profiles_df.iterrows():
                        full_name = row["Full Name"]
                        linkedin_url = row.get("LinkedIn") or row.get("LinkedIn URL") or row.get("linkedin_url", "")
                        
                        # Initialize note field if not present
                        if linkedin_url not in st.session_state.outreach_notes:
                            st.session_state.outreach_notes[linkedin_url] = ""

                        st.session_state.outreach_notes[linkedin_url] = st.text_area(
                            label=f"Notes for {full_name}",
                            key=f"note_{linkedin_url}",
                            value=st.session_state.outreach_notes[linkedin_url],
                            placeholder="Add notes here...",
                            height=100
                        )

                # if st.button("📩 Log Outreach", use_container_width=True):
                if st.button("📩 Log Outreach", use_container_width=True):
                    try:
                        insert_query = """
                            INSERT INTO LINKEDIN.PUBLIC.PROSPECT_TOUCH_LOG 
                            (linkedin_url, contacted_by, contact_method, notes)
                            VALUES (?, ?, ?, ?)
                        """

                        count_logged = 0
                        for _, row in selected_profiles_df.iterrows():
                            linkedin_url = row.get("LinkedIn") or row.get("LinkedIn URL") or row.get("linkedin_url", "")
                            contacted_by = st.session_state.username
                            contact_method = "outreach_message"
                            notes = st.session_state.outreach_notes.get(linkedin_url, "")

                            if linkedin_url:
                                session.sql(insert_query, params=[
                                    linkedin_url,
                                    contacted_by,
                                    contact_method,
                                    notes
                                ]).collect()
                                count_logged += 1

                                # Safely clear notes
                                if linkedin_url in st.session_state.outreach_notes:
                                    del st.session_state.outreach_notes[linkedin_url]

                        st.success(f"✅ Outreach logged for {count_logged} profile(s).")
                        st.rerun()

                    except Exception as e:
                        st.error(f"⚠️ Error logging outreach: {e}")




            

    else:
        st.warning("Please search for profiles before using this feature.")    
        if st.button("Go to Prospect Finder", use_container_width=True, type="primary"):
            st.switch_page("files/Prospect_Finder.py")
        if st.session_state.logged_in and st.session_state.username != 'guest':
            if st.button("Go to Chat History", use_container_width=True):
                st.switch_page("files/Chat_History.py")