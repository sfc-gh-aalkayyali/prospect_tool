import streamlit as st
import uuid
import os
from functions.helper_global import *
from datetime import datetime
import fitz


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

st.title("📝 Prospect Documents Manager")
st.markdown("---")

if st.session_state.logged_in: 
    session = create_session()

    username = st.session_state["username"]

    adding_customer_document = f"""INSERT INTO CUSTOMER_DOCUMENTS(ID, Username, Customer, Title, Content, Date) VALUES(?, ?, ?, ?, ?, ?)"""

    st.markdown("### Add a New Prospect Document")
    upload_option = st.selectbox(label="Select your preferred method to upload", options=["Upload PDF", "Manually Enter"])
    if upload_option == "Upload PDF":
        columns = st.columns(2)
        with columns[0]:
            company_name = st.text_input(label="Company", placeholder="Enter the Company Name...", key="customer_company")
        with columns[1]:
            document_title = st.text_input(label="Document Title", placeholder="Enter the Document Title...", key="customer_title")
        file = st.file_uploader(label="Upload your customer document", type="pdf", key="customer_content_pdf", accept_multiple_files=False)

        if file:
            with st.spinner("Processing PDF...", show_time=True):
                file.seek(0)
                pdf_bytes = file.read()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")

                full_text = ""
                combined_text = ""
                all_stories = []

                for page_number, page in enumerate(doc, start=1):
                    page_text = page.get_text()
                    combined_text += f"Page {page_number}\n\n" + page_text + "\n\n"

            combined_text = re.sub(r'\n{3,}', '\n\n', combined_text)

            with st.container(height=500):
                st.write(combined_text)

            if st.button("Add Prospect Document", use_container_width=True, key=f"add_story_{page_number}"):
                if not company_name.strip():
                    st.warning("Please enter the company name before saving.")
                elif not document_title.strip():
                    st.warning("Please enter the document title before saving.")
                else:
                    try: 
                        id = uuid.uuid4()
                        session.sql(adding_customer_document, params=[str(id), username, st.session_state.customer_company, st.session_state.customer_title, combined_text, datetime.now()]).collect()
                        st.toast("Added Prospect Document.", icon="🎉")
                    except Exception as e:
                        st.error(f"Error adding story: {e}")
                combined_text = ""
                        
    elif upload_option == "Manually Enter":

        columns = st.columns(2)
        with columns[0]:
            company_name = st.text_input(label="Company", placeholder="Enter the Company Name...", key="customer_company2")
        with columns[1]:
            document_title = st.text_input(label="Document Title", placeholder="Enter the Document Title...", key="customer_title2")
        customer_text = st.text_area(label="Prospect Document Text", placeholder="Enter the Document Text...", key="document_text")

        if st.button("Save Prospect Document", use_container_width=True, type='primary'):
            if not company_name.strip():
                st.warning("Please enter the company name before saving.")
            elif not document_title.strip():
                st.warning("Please enter the document title before saving.")
            elif not customer_text.strip():
                st.warning("Please enter the document content before saving.")
            else:
                id = str(uuid.uuid4())
                with st.spinner(text="In progress...",  show_time=True):
                    try:
                        session.sql(adding_customer_document, params=[str(id), username, st.session_state.customer_company2, st.session_state.customer_title2, customer_text, datetime.now()]).collect()
                    except Exception as e:
                        st.error(f"Error saving template: {e}")

    st.markdown("---")

    # 📌 Section: Manage Your Prospect Documents
    st.markdown("### Manage Your Prospect Documents")

    query = f"""
        SELECT * FROM CUSTOMER_DOCUMENTS 
        WHERE USERNAME = ? ORDER BY DATE
    """
    stories = session.sql(query, params=[username]).collect()


    if not stories:
        st.info("You have no customer documents yet.")
    else:
        # Search bar
        st.text_input("Search Prospect Documents", key='document_search', placeholder="Type to search...").strip().lower()

        filtered_stories = [story for story in stories if st.session_state.document_search in story["CONTENT"].lower()]

        if st.session_state.document_search and not filtered_stories:
            st.warning("No customer stories found.")
            if st.button("Reset Search", key="reset_document_search", use_container_width=True):
                if st.session_state.document_search:
                    del st.session_state.document_search
                    st.session_state.document_search = ''
                st.rerun()

        if filtered_stories:
            with st.container(height=350):  
                for number, story in enumerate(filtered_stories, start=1):
                    story_id = story["ID"]
                    date_added = story["DATE"]
                    title = story["TITLE"]
                    customer = story["CUSTOMER"]
                    text = story["CONTENT"]

                    with st.expander(f"Document for {customer} - {title}"):
                        updated_name = st.text_input("Prospect Name", customer, key=f"industry_{story_id}")
                        updated_title = st.text_input("Prospect Title", title, key=f"title_{story_id}")
                        updated_text = st.text_area("Prospect Document", text, height=150, key=f"story_{story_id}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Update", key=f"update_{story_id}", use_container_width=True):
                                update_query = """
                                    UPDATE CUSTOMER_DOCUMENTS 
                                    SET CONTENT = ?,
                                    TITLE = ?,
                                    CUSTOMER = ?
                                    WHERE ID = ?
                                """
                                try:
                                    session.sql(update_query, params=[updated_text, updated_title, updated_name, story_id]).collect()
                                    st.toast(f"Updated story for {updated_name}.", icon="🎉")
                                except Exception as e:
                                    st.error(e)
                                

                        with col2:
                            if st.button("Delete", key=f"delete_{story_id}", use_container_width=True):
                                delete_query = "DELETE FROM CUSTOMER_DOCUMENTS WHERE ID = ?"
                                try:
                                    session.sql(delete_query, params=[story_id]).collect()
                                    st.toast(f"Deleted story for {updated_name}.", icon="🎉")
                                    st.rerun()
                                except Exception as e:
                                    st.error(e)

# 📌 Section: Navigation Buttons
if st.button("Go to Message Generation", use_container_width=True):
    st.switch_page("files/Message_Generation.py")