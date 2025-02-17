import streamlit as st

@st.cache_resource
def create_session():
    ### creating session for Streamlit in Snowflake (SiS)
    try:
        from snowflake.snowpark import Session
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
    ### creating session for local development via python connector using credentials found in config.toml file.
    except:
        from snowflake.snowpark import Session
        session = Session.builder.config("connection_name", "my_conn").create()
    
    session.sql("USE DATABASE LINKEDIN").collect()
    return session