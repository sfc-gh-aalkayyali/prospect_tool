
import os
from snowflake.snowpark import Session
from snowflake.snowpark.exceptions import *
import streamlit as st

# Environment variables below will be automatically populated by Snowflake.
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_HOST = os.getenv("SNOWFLAKE_HOST")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")

# Custom environment variables
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")

def get_login_token():
    """
    Read the login token supplied automatically by Snowflake. These tokens
    are short lived and should always be read right before creating any new connection.
    """
    with open("/snowflake/session/token", "r") as f:
        return f.read()

def get_connection_params():
    """
    Construct Snowflake connection params from environment variables.
    """
    if os.path.exists("/snowflake/session/token"):
        return {
            "account": SNOWFLAKE_ACCOUNT,
            "host": SNOWFLAKE_HOST,
            "authenticator": "oauth",
            "token": get_login_token(),
            "warehouse": SNOWFLAKE_WAREHOUSE,
            "database": SNOWFLAKE_DATABASE,
            "schema": SNOWFLAKE_SCHEMA
        }
    else:
        return {
            "account": SNOWFLAKE_ACCOUNT,
            "host": SNOWFLAKE_HOST,
            "user": SNOWFLAKE_USER,
            "password": SNOWFLAKE_PASSWORD,
            "role": SNOWFLAKE_ROLE,
            "warehouse": SNOWFLAKE_WAREHOUSE,
            "database": SNOWFLAKE_DATABASE,
            "schema": SNOWFLAKE_SCHEMA
        }

@st.cache_resource
def create_session():
    try:
        session = Session.builder.configs(get_connection_params()).create()
        session.sql("USE WAREHOUSE COMPUTE_WH").collect()
        session.sql("USE DATABASE LINKEDIN").collect()
    except:
        from snowflake.snowpark import Session
        session = Session.builder.config("connection_name", "my_conn").create()
        session.sql("USE DATABASE LINKEDIN").collect()
    return session

# @st.cache_resource
# def create_session():
#     ### creating session for Streamlit in Snowflake (SiS)
#     try:
#         from snowflake.snowpark import Session
#         from snowflake.snowpark.context import get_active_session
#         session = get_active_session()
#     ### creating session for local development via python connector using credentials found in config.toml file.
#     except:
#         import json
#         from snowflake.snowpark import Session
#         with open("credentials.json", "r") as file:
#             config = json.load(file)

#             # Configure Snowflake connection with browser authentication
#             connection_parameters = {
#                 "account": config["account"],
#                 "password": config["password"],
#                 "user": config["user"],
#                 "authenticator": "username_password_mfa",
#                 "role": config["role"],
#                 "warehouse": config["warehouse"],
#                 "database": config["database"],
#                 "schema": config["schema"],
#                 "ocsp_fail_open": False,
#             }

#             # Create and return a Snowflake session
#             session = Session.builder.configs(connection_parameters).create()
#             return session