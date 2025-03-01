from functions.helper_global import *
from functions.helper_finder import *
from functions.helper_session import *
import pandas as pd
from datetime import datetime
import uuid
from functions.helper_session import *
from st_aggrid import AgGrid, GridOptionsBuilder


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
            
html_code = f"""
<div id="scroll-to-me" style='background: transparent; height:1px;'></div>
<script>
var e = document.getElementById("scroll-to-me");
if (e) {{
    e.scrollIntoView({{behavior: "smooth"}});
    e.remove();
}}
</script>
"""
icons = {"assistant": "🕵️‍♂️", "user": "👤"}

init_service_metadata()

search_profile_toggle = st.sidebar.toggle("Search Profiles", value=True, key="search_profiles", help="If toggle is on it will activate Cortex Search to retrieve profiles when you query the chatbot. Conversely, if it is off you can query the LLM without retrieving profiles.")

if search_profile_toggle:
    if st.session_state.temperature:
        del st.session_state.temperature
        st.session_state.temperature = 0.0
    
    if st.session_state.top_p:
        del st.session_state.top_p
        st.session_state.top_p = 1.0
    st.session_state.model = 'llama3.1-70b'

    classifications = session.sql('SELECT DISTINCT CLASSIFICATION FROM LINKEDIN.PUBLIC."LinkedIn Accounts Cortext"').to_pandas()
    classifications = classifications.dropna().loc[classifications['CLASSIFICATION'].str.strip() != '']

    company_name = session.sql('SELECT DISTINCT COMPANYNAME FROM LINKEDIN.PUBLIC."LinkedIn Accounts Cortext"').to_pandas()
    company_name = company_name.dropna().loc[company_name['COMPANYNAME'].str.strip() != '']

    industries = session.sql('SELECT DISTINCT INDUSTRY FROM LINKEDIN.PUBLIC."LinkedIn Accounts Cortext"').to_pandas()
    industries = industries.dropna().loc[industries['INDUSTRY'].str.strip() != '']

    locations = session.sql('SELECT DISTINCT LOCATION FROM LINKEDIN.PUBLIC."LinkedIn Accounts Cortext"').to_pandas()
    locations = locations.dropna().loc[locations['LOCATION'].str.strip() != '']

    connection_degrees = session.sql('SELECT DISTINCT CONNECTIONDEGREE FROM LINKEDIN.PUBLIC."LinkedIn Accounts Cortext"').to_pandas()
    connection_degrees = connection_degrees.dropna().loc[connection_degrees['CONNECTIONDEGREE'].astype(str).str.strip() != '']

    with st.sidebar.expander("Cortex Search Filters", expanded=True):

        st.multiselect(
            "Location",
            locations,
            key="location_filter"
        )

        st.multiselect(
            "Industry",
            industries,
            key="industry_filter"
        )

        st.multiselect(
            "Company Name",
            company_name,
            key="company_filter"
        )
            
        st.multiselect(
            "Classification",
            classifications,
            key="classification_filter"
        )

        st.multiselect(
            "Connection Degree",
            connection_degrees,
            key="connectiondegree_filter"
        )

        st.markdown("---")

        st.slider(
        "Select number of documents to retrieve",
        key="general_num_retrieved_chunks",
        min_value=1,
        value=80,
        max_value=300,
        help="*Limits the maximum number of documents returned from Cortex Search. A higher number will affect performace.*"
    )

        if st.session_state.general_people != []:
            formatted_people = [p.replace("\n", "<br>") for p in st.session_state.general_people]
            with st.container(height=300):
                st.write("Cortex Search Documents")
                for i, person in enumerate(formatted_people, start=1):
                    st.markdown(f"**Option {i}:**<br>{person}", unsafe_allow_html=True)
                    st.write("---")
else:
    st.session_state.temperature = 0.5
    st.session_state.top_p = 1.0

init_config_options_finder()
if st.sidebar.button("Clear Conversation", use_container_width=True, type="secondary"):
    del st.session_state.general_messages
    del st.session_state.general_chat_history
    del st.session_state.service_metadata
    del st.session_state.general_people
    del st.session_state.selected_prompt
    del st.session_state.chat_id
    st.session_state.chat_id = uuid.uuid4()
    if 'connectiondegree_filter' in st.session_state:
        del st.session_state.connectiondegree_filter
        st.session_state.connectiondegree_filter = []

    if 'classification_filter' in st.session_state:
        del st.session_state.classification_filter
        st.session_state.classification_filter = []
    
    if 'company_filter' in st.session_state:
        del st.session_state.company_filter
        st.session_state.company_filter = []

    if 'industry_filter' in st.session_state:
        del st.session_state.industry_filter
        st.session_state.industry_filter = []

    if 'location_filter' in st.session_state:
        del st.session_state.location_filter
        st.session_state.location_filter = []

    st.rerun()

def save_chat_history():
    if st.session_state.logged_in and st.session_state.username != "guest":
        save_chat(datetime.now(), st.session_state.username, st.session_state.chat_id, generate_chat_title(st.session_state.chat_id, st.session_state.username, st.session_state.general_messages), st.session_state.general_messages, st.session_state.general_chat_history)

st.title(f":mag: Prospect Finder")
st.markdown("---")

suggested_prompts = [
    "Retrieve 5 Data Engineers who have over 10 years of experience and extensive knowledge of related technologies.",
    "What technologies do Data Scientists typically use?",
    "How can Snowflake appeal to a customer?"
]

for index, prompt in enumerate(suggested_prompts):
    if st.button(prompt, use_container_width=True, key=f"general_prompt_{index}"):
        st.session_state.selected_prompt = prompt

if st.session_state.selected_prompt and st.session_state.selected_prompt != None:    
    st.session_state.general_messages.append({"role": "user", "content": st.session_state.selected_prompt})

    with st.chat_message("assistant", avatar=icons["assistant"]):
        with st.spinner("Thinking...",  show_time=True):
            if search_profile_toggle:
                try:
                    generated_response = table_complete_function(create_table_prompt(st.session_state.selected_prompt))
                except Exception as e:
                    generated_response = "text", f"An error occurred: {e}"
            else:
                try:
                    generated_response = complete_function(create_query_prompt(st.session_state.selected_prompt))
                except Exception as e:
                    generated_response = "text", f"An error occurred: {e}"

            st.session_state.general_messages.append(
                {"role": "assistant", "content": generated_response}
            )
            save_chat_history()     

    st.session_state.selected_prompt = None
    st.rerun()

general_table_index = 1
# Loop through messages to display in chat
for index, message in enumerate(st.session_state.general_messages):
    with st.chat_message(message["role"], avatar=icons[message["role"]]):
        if isinstance(message["content"], pd.DataFrame):

            dataframe = message["content"].copy()

            # Create GridOptions
            gb = GridOptionsBuilder.from_dataframe(dataframe)

            # Enable sorting and resizing globally
            gb.configure_default_column(sortable=True, resizable=True, wrapText=True, autoHeight=True)

            # Enable filtering for specific columns
            filterable_columns = [
                "Full Name",
                "Company Name",
                "Industry",
                "Job Title",
                "Classification",
                "Location",
                "Duration In Role",
                "Duration At Company",
                "Connection Degree",
                "Shared Connections"
            ]

            for col in filterable_columns:
                if col in dataframe.columns:
                    gb.configure_column(col, filterable=True, filter="agSetColumnFilter")  # Enables dropdown-based filter


            # Enable word wrapping for text-heavy columns
            expandable_columns = ["Profile Summary", "Job Description"]
            for col in expandable_columns:
                gb.configure_column(
                    col,
                    editable=True, 
                    cellEditor="agLargeTextCellEditor", 
                    cellEditorPopup=True,
                    width=200,  # Strict column width
                    maxWidth=200,  # Prevents column from stretching
                    minWidth=200,  # Ensures consistency
                    cellStyle={'overflow': 'hidden', 'textOverflow': 'ellipsis', 'whiteSpace': 'nowrap'}
                )
            # Enable pagination
            grid_options = gb.build()
        
            # Display the AgGrid
            row_height = 40  # Approximate row height in pixels
            max_visible_rows = min(len(dataframe), 10)  # Show up to 10 rows by default
            dynamic_height = max(200, max_visible_rows * row_height)  # Minimum height of 200px

            grid_response = AgGrid(dataframe, 
                gridOptions=grid_options, 
                height=dynamic_height,  # Apply dynamic height
                enable_enterprise_modules=True, 
                pagination=True, 
                paginationPageSize=20)
            
            filtered_df = pd.DataFrame(grid_response['data'])

            if st.session_state.generated_profiles:
                del st.session_state.generated_profiles
                st.session_state.generated_profiles = []

            st.session_state.generated_profiles.extend(filtered_df.to_dict(orient="records"))

            if st.button(f"Send Profiles to Message Generation", key=f"general_generate_messages_{general_table_index}"):
                if not filtered_df.empty and "Full Name" in filtered_df.columns:
                    st.session_state.profile_selection = filtered_df["Full Name"].tolist()
                    st.session_state.general_profiles = filtered_df  # Ensure the full profile data is stored
                    st.success(f"Successfully sent {len(filtered_df)} profiles to Message Generator")
                    st.switch_page("pages/Message_Generation.py")
                else:
                    st.warning("No profiles selected or data missing!")
            csv_data = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"Download Table {general_table_index}",
                data=csv_data,
                file_name=f"filtered_profiles_{general_table_index}_{datetime.now()}.csv",
                mime="text/csv"
            )
            general_table_index += 1
        else:
            st.markdown(message["content"])
    # Ensure new messages scroll into view
    components.html(html_code, height=0)


# Chat input for user
question = st.chat_input("Ask a question...", disabled=("service_metadata" not in st.session_state or len(st.session_state.service_metadata) == 0))

if question:
    st.session_state.general_messages.append({"role": "user", "content": question})
    
    with st.chat_message("user", avatar=icons["user"]):
        st.markdown(question)

    with st.chat_message("assistant", avatar=icons["assistant"]):
        with st.spinner("Thinking...",  show_time=True):
            if search_profile_toggle:
                try:
                    generated_response = table_complete_function(create_table_prompt(question))
                except Exception as e:
                    generated_response = "text", f"An error occurred: {e}"
            else:
                try:
                    generated_response = complete_function(create_query_prompt(question))
                except Exception as e:
                    generated_response = "text", f"An error occurred: {e}"

            st.session_state.general_messages.append({"role": "assistant", "content": generated_response})
            save_chat_history()
    st.rerun()