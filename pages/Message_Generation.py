from functions.helper_global import *
from functions.helper_generation import *
from functions.helper_session import *
import pandas as pd

init_service_metadata()
init_config_options()
init_session_state()

with st.sidebar.expander("Message Generation Advanced Options"):
    st.text_area("System Prompt:", value=st.session_state.message_system_prompt, height=300, key="updated_message_system_prompt")
    if st.button("Submit System Prompt", use_container_width=True, key="message_system", type="primary"):
        st.session_state.message_system_prompt = st.session_state.updated_message_system_prompt
        st.success("Successfully Added Prompt")

if st.sidebar.button("Clear Selections", use_container_width=True, type="secondary"):
    del st.session_state.service_metadata
    del st.session_state.generated_messages
    del st.session_state.uploaded_emails
    del st.session_state.customer_stories_docs
    del st.session_state.selected_customer_stories_docs
    st.session_state.customer_stories_docs = []
    st.session_state.uploaded_emails = ""
    st.session_state.persona_profile_selection = []
    st.session_state.general_profile_selection = []
    st.session_state.selected_customer_stories_docs = []
    st.rerun()

st.title(":speech_balloon: Message Generation")
st.write("")

col1, col2 = st.columns(2)

with col1: 
    option = st.selectbox(
        "Select retrieved profiles",
        ["General Finder", "Persona Finder"]
    )

    if option == "General Finder":
        people_df = st.session_state.general_profiles
    elif option == "Persona Finder":
        people_df = st.session_state.persona_profiles
    else:
        people_df = pd.DataFrame()

if not people_df.empty:  
    with col2:
        people_df['Full Name'] = people_df['First Name'] + " " + people_df['Last Name']
        people_df = people_df.drop_duplicates(subset=['Full Name'])

        if option == "General Finder":
            selected_names = st.multiselect("Select Profiles:", people_df['Full Name'].tolist(), default=(st.session_state.general_profile_selection), key="profile_selection")
        elif option == "Persona Finder":
            selected_names = st.multiselect("Select Profiles:", people_df['Full Name'].tolist(), default=(st.session_state.persona_profile_selection), key="profile_selection")

    selected_profiles_df = people_df[people_df['Full Name'].isin(selected_names)]

    if option == "General Finder":
        if st.session_state.general_chat_history != "":
            with st.sidebar.container(height=150):
                st.write("General Chat history summary")
                st.markdown(st.session_state.general_chat_history)
    elif option == "Persona Finder":
        if st.session_state.persona_chat_history != "":
            with st.sidebar.container(height=150):
                st.write("Persona Chat history summary")
                st.markdown(st.session_state.persona_chat_history)

    if not selected_profiles_df.empty:
        st.markdown("### Selected Profile Details:")
        with st.container(height=300):
            for index, row in selected_profiles_df.iterrows():
                profile_details = "\n".join([f"{col}: {val}" for col, val in row.items() if col not in ["Full Name"]])
                st.text_area(f"Profile: {row['Full Name']}", value=profile_details, height=200)

        # ✅ Only show this section if at least one profile is selected
        if selected_profiles_df.shape[0] > 0:
            st.markdown("---")
            st.markdown("### Options for Message Generation:")

            col3, col4 = st.columns(2)

            with col3:
                st.multiselect(
                "Industry Customer Stories to Retreive",
                ["Telecommunication"],
                help="These options will filter the customer stories based on Industry.",
                key="customer_stories_filter"
            )
            with col4:
                st.text_input(label="Enter a keyword to search on:", placeholder="Type here...", key="customer_stories_search", help="Search any keyterm to identify companies/industries you are looking for.",)

            st.slider(label="Limit stories retreived:",min_value=1, max_value=8, value=3, key="customer_stories_limit")

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
            preselected_emails = st.selectbox("Optionally Choose an Email Template", ("Marketing Message", "ESG Message", "Splunk Message"), index=None)
            if preselected_emails == None:
                st.session_state.email_placeholder = ""
            elif preselected_emails == "Marketing Message":
                # uploaded_files = st.session_state.marketing_message
                st.session_state.email_placeholder = st.session_state.marketing_message
            elif preselected_emails == "ESG Message":
                # uploaded_files = st.session_state.ESG_message
                st.session_state.email_placeholder = st.session_state.ESG_message
            elif preselected_emails == "Splunk Message":
                # uploaded_files = st.session_state.splunk_message
                st.session_state.email_placeholder = st.session_state.splunk_message

            uploaded_files = st.text_area(label="Sample Email", value=st.session_state.email_placeholder, placeholder="Type sample email here...", help="Type in a sample email to pass into the LLM to follow the same structure.", height=250)
            
            if st.button(label="Add Sample Email", use_container_width=True):
                st.session_state.uploaded_emails = uploaded_files
                st.success("Successfully Added Email")

            # ✅ "Generate All Messages" Button
            if st.button("Generate All Messages", use_container_width=True, type="primary"):
                with st.spinner("Generating messages..."):
                    generated_messages = {
                        f"{row['First Name']} {row['Last Name']}": complete_function(create_direct_message(row.to_dict(), option))
                        for _, row in selected_profiles_df.iterrows()
                    }
                    st.session_state.generated_messages = generated_messages

            # ✅ Display Generated Messages with 📥 Download Icon
            if st.session_state.generated_messages:
                st.markdown("### Generated Messages:")
                all_messages = ""
                
                for name, message in st.session_state.generated_messages.items():
                    col1, col2 = st.columns([0.9, 0.1])  # Message box & download icon

                    with col1:
                        st.text_area(f"Generated Message for {name}:", value=message, height=250, key=f"text_{name}")

                    with col2:
                        text_bytes = text_download(message)
                        st.download_button(
                            label="📥",  # Download icon only
                            data=text_bytes,
                            file_name=f"{name.replace(' ', '_')}_message.txt",
                            mime="text/plain",
                            key=f"download_{name}",
                            help=f"Download {name}'s message"
                        )

                    all_messages += f"Message for {name}:\n{message}\n\n" + "-" * 60 + "\n\n"

                # ✅ "Download All Messages" Button
                all_text_bytes = text_download(all_messages)
                st.download_button(
                    label="Download All Messages",
                    data=all_text_bytes,
                    file_name="all_generated_messages.txt",
                    mime="text/plain",
                    use_container_width=True,
                    type="primary"
                )
else:
    st.info("Please search for profiles before using this feature.")
