import streamlit as st
import pandas as pd
from functions.helper_outreach import get_outreach_logs_with_names
from functions.helper_global import init_session_state, create_session

# Initialize session state and DB
init_session_state()
session = create_session()
username = st.session_state.username

# st.set_page_config(page_title="Outreach Tracker", layout="wide")
st.title("📊 Outreach Tracker")
st.markdown("---")

# Get outreach logs
logs_df = get_outreach_logs_with_names(session, username)

if logs_df.empty:
    st.info("No outreach logs found yet.")
else:
    # Format contacted_on
    logs_df["contacted_on"] = pd.to_datetime(logs_df["contacted_on"]).dt.strftime("%b %d, %Y %H:%M")

    # Create HTML links for LinkedIn URL
    logs_df["linkedin_url"] = logs_df["linkedin_url"].apply(
        lambda url: f"<a href='{url}' target='_blank'>View Profile</a>" if url else ""
    )

    # Filters
    with st.expander("🔍 Filter Options", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_names = st.multiselect("Filter by Full Name", sorted(logs_df["full_name"].dropna().unique()))
        with col2:
            selected_contacted_by = st.multiselect("Filter by Contacted By", sorted(logs_df["contacted_by"].dropna().unique()))
        with col3:
            selected_urls = st.multiselect("Filter by LinkedIn URL", sorted(logs_df["linkedin_url"].dropna().unique()))

        if selected_names:
            logs_df = logs_df[logs_df["full_name"].isin(selected_names)]
        if selected_contacted_by:
            logs_df = logs_df[logs_df["contacted_by"].isin(selected_contacted_by)]
        if selected_urls:
            logs_df = logs_df[logs_df["linkedin_url"].isin(selected_urls)]

        if st.button("Reset Filters"):
            st.rerun()

    st.markdown("### 📁 Contact History")
    logs_df.rename(columns={
        "linkedin_url": "LinkedIn URL",
        "contacted_by": "Contacted By",
        "contact_method": "Method",
        "contacted_on": "Date",
        "notes": "Notes",
        "full_name": "Full Name"
    }, inplace=True)

    # Reorder columns if needed
    column_order = ["Full Name", "LinkedIn URL", "Contacted By", "Method", "Date", "Notes"]
    logs_df = logs_df[column_order]

    # Render styled HTML table
    st.write(logs_df.to_html(escape=False, index=False), unsafe_allow_html=True)
