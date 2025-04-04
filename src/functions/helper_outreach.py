from snowflake.snowpark import Session
import pandas as pd

def get_outreach_logs_with_names(session, username):
    query = """
    SELECT 
        p.linkedin_url,
        p.contacted_by,
        p.contact_method,
        p.contacted_on,
        p.notes,
        a.fullname
    FROM LINKEDIN.PUBLIC.PROSPECT_TOUCH_LOG p
    LEFT JOIN LINKEDIN.PUBLIC."LinkedIn Accounts" a
        ON p.linkedin_url = a.LINKEDINPROFILEURL
    WHERE p.contacted_by = ?
    ORDER BY p.contacted_on DESC
"""

    df = session.sql(query, params=[username]).to_pandas()
    df.columns = [col.lower() for col in df.columns]  # normalize
    return df

