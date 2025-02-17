from functions.helper_global import *
from functions.helper_finder import *
from functions.helper_session import *
import pandas as pd
from functions.helper_session import *

## State Session Variables


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

init_session_state()
init_service_metadata()
init_config_options_finder()


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

with st.sidebar.expander("Cortex Search Options", expanded=True):

    st.write("Filter Results")

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
    
    # st.text_area("System Prompt:", value=st.session_state.general_system_prompt, height=300, key="updated_general_system_prompt")
    # if st.button("Submit System Prompt", use_container_width=True, key="general_system", type="primary"):
    #     st.session_state.general_system_prompt = st.session_state.updated_general_system_prompt
    #     st.success("Successfully Added Prompt")

    # if st.session_state.general_chat_history != "":
    #     with st.container(height=150):
    #         st.write("Chat history summary")
    #         st.markdown(st.session_state.general_chat_history)

    if st.session_state.general_people != []:
        formatted_people = [p.replace("\n", "<br>") for p in st.session_state.general_people]
        with st.container(height=300):
            st.write("Cortex Search Documents")
            for i, person in enumerate(formatted_people, start=1):
                st.markdown(f"**Option {i}:**<br>{person}", unsafe_allow_html=True)
                st.write("---")
    
if st.sidebar.button("Clear Conversation", use_container_width=True, type="secondary"):
    del st.session_state.general_messages
    del st.session_state.general_chat_history
    del st.session_state.service_metadata
    del st.session_state.general_people
    del st.session_state.selected_prompt
    del st.session_state.general_generated_messages
    del st.session_state.connectiondegree_filter
    del st.session_state.classification_filter
    del st.session_state.company_filter
    del st.session_state.industry_filter
    del st.session_state.location_filter
    st.session_state.connectiondegree_filter = []
    st.session_state.classification_filter = []
    st.session_state.company_filter = []
    st.session_state.industry_filter = []
    st.session_state.location_filter = []
    st.rerun()


st.title(f":mag: General Finder")
st.write("")

suggested_prompts = [
    "Retrieve 5 Data Engineers who have over 10 years of experience and use Hadoop or similar technologies.",
    "What technologies do Data Scientists at Telstra typically use?",
    "How many employees does Telstra have? How can Snowflake add value to Telstra?"
]

for index, prompt in enumerate(suggested_prompts):
    if st.button(prompt, use_container_width=True, key=f"general_prompt_{index}"):
        st.session_state.selected_prompt = prompt

if st.session_state.selected_prompt and st.session_state.selected_prompt != None:    
    st.session_state.general_messages.append({"role": "user", "content": st.session_state.selected_prompt})

    with st.chat_message("assistant", avatar=icons["assistant"]):
        with st.spinner("Thinking..."):
            try:
                generated_response = table_complete_function(create_prompt_general(st.session_state.selected_prompt))
            except Exception as e:
                generated_response = "text", f"An error occurred: {e}"

            st.session_state.general_messages.append(
                {"role": "assistant", "content": generated_response}
            )

    st.session_state.selected_prompt = None
    st.rerun()

general_table_index = 1
# Loop through messages to display in chat
for index, message in enumerate(st.session_state.general_messages):
    with st.chat_message(message["role"], avatar=icons[message["role"]]):
        if isinstance(message["content"], pd.DataFrame):
        
            df = message["content"]
            # filtered_df = df.copy()

            available_columns = df.columns.tolist()

            st.session_state.general_profiles = pd.concat([st.session_state.general_profiles, df], ignore_index=True)
            filtered_df = df.copy()

            with st.sidebar.expander(f"Filter Table {general_table_index}"):
                unique_key_prefix = f"general_filter_{general_table_index}"

                if "Title" in available_columns:
                    filter_title = st.multiselect(
                        "Title", df["Title"].unique(), 
                        default=df["Title"].unique(), 
                        key=f"{unique_key_prefix}_title"
                    )
                    filtered_df = filtered_df[filtered_df["Title"].isin(filter_title)]

                if "Classification" in available_columns:
                    filter_classification = st.multiselect(
                        "Classification", df["Classification"].unique(), 
                        default=df["Classification"].unique(), 
                        key=f"{unique_key_prefix}_classification"
                    )
                    filtered_df = filtered_df[filtered_df["Classification"].isin(filter_classification)]

                if "Company" in available_columns:
                    filter_company = st.multiselect(
                        "Company", df["Company"].unique(), 
                        default=df["Company"].unique(), 
                        key=f"{unique_key_prefix}_company"
                    )
                    filtered_df = filtered_df[filtered_df["Company"].isin(filter_company)]

                if "Location" in available_columns:
                    filter_location = st.multiselect(
                        "Location", df["Location"].unique(), 
                        default=df["Location"].unique(), 
                        key=f"{unique_key_prefix}_location"
                    )
                    filtered_df = filtered_df[filtered_df["Location"].isin(filter_location)]

                if "Industry" in available_columns:
                    filter_industry = st.multiselect(
                        "Industry", df["Industry"].unique(), 
                        default=df["Industry"].unique(), 
                        key=f"{unique_key_prefix}_industry"
                    )
                    filtered_df = filtered_df[filtered_df["Industry"].isin(filter_industry)]

                if "Connection Degree" in available_columns:
                    filter_connection_degree = st.multiselect(
                        "Connection Degree", df["Connection Degree"].unique(), 
                        default=df["Connection Degree"].unique(), 
                        key=f"{unique_key_prefix}_connection_degree"
                    )
                    filtered_df = filtered_df[filtered_df["Connection Degree"].isin(filter_connection_degree)]

                if "Shared Connections" in available_columns:
                    filtered_df["Shared Connections"] = filtered_df["Shared Connections"].apply(convert_to_int)
                    min_shared, max_shared = get_slider_range(filtered_df, "Shared Connections")
                    filter_shared_connections = st.slider(
                        "Shared Connections", min_value=min_shared, max_value=max_shared, 
                        value=(min_shared, max_shared), key=f"{unique_key_prefix}_shared_connections"
                    )
                    filtered_df = filtered_df[filtered_df["Shared Connections"].between(filter_shared_connections[0], filter_shared_connections[1])]

                if "Duration in Role" in available_columns:
                    filtered_df["Months in Role"] = filtered_df["Duration in Role"].apply(convert_duration_to_months)
                    min_role_duration, max_role_duration = get_slider_range(filtered_df, "Months in Role")
                    filter_duration_role = st.slider(
                        "Duration in Role (Months)", min_value=min_role_duration, max_value=max_role_duration, 
                        value=(min_role_duration, max_role_duration), key=f"{unique_key_prefix}_duration_role"
                    )
                    filtered_df = filtered_df[filtered_df["Months in Role"].between(filter_duration_role[0], filter_duration_role[1])]

                if "Duration in Company" in available_columns:
                    filtered_df["Months in Company"] = filtered_df["Duration in Company"].apply(convert_duration_to_months)
                    min_company_duration, max_company_duration = get_slider_range(filtered_df, "Months in Company")
                    filter_duration_company = st.slider(
                        "Duration in Company (Months)", min_value=min_company_duration, max_value=max_company_duration, 
                        value=(min_company_duration, max_company_duration), key=f"{unique_key_prefix}_duration_company"
                    )
                    filtered_df = filtered_df[filtered_df["Months in Company"].between(filter_duration_company[0], filter_duration_company[1])]

            # 🔹 Display Filtered DataFrame
            st.dataframe(
                filtered_df, 
                hide_index=True,
                use_container_width=True,
                column_order=[col for col in [
                    "First Name",
                    "Last Name",
                    "Title",
                    "Classification",
                    "Location",
                    "Company",
                    "Industry",
                    "Connection Degree",
                    "Shared Connections",
                    "Duration in Role",
                    "Duration in Company",
                    "Title Description",
                    "Summary",
                    "LinkedIn Profile URL",
                ] if col in filtered_df.columns.tolist()]
            )

            if st.button(f"Send Profiles from Table {general_table_index} to Message Generation", key=f"general_generate_messages_{general_table_index}"):
                filtered_df['Full Name'] = filtered_df['First Name'] + " " + filtered_df['Last Name']
                people_df = filtered_df.drop_duplicates(subset=['Full Name'])
                st.session_state.general_profile_selection = people_df['Full Name'].tolist()
                st.success(f"Successfully Added Profiles from Table {general_table_index} to Message Generator")

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
        with st.spinner("Thinking..."):
            try:
                generated_response = table_complete_function(create_prompt_general(question))
            except Exception as e:
                generated_response = "text", f"An error occurred: {e}"

            st.session_state.general_messages.append({"role": "assistant", "content": generated_response})
    st.rerun()