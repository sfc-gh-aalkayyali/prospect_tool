import streamlit as st
import functions.helper_global


def create_direct_message(profile, flagger):
    system_prompt = st.session_state.message_system_prompt

    # Initialize placeholders for email and story sections
    email_content = ""
    story_content = ""
    chat_history = ""

    if st.session_state.general_chat_history != "" and flagger == "General Finder":
            chat_history += f"""
<chat_history>
{st.session_state.general_chat_history }
</chat_history>
"""
    if st.session_state.persona_chat_history != "" and flagger == "Persona Finder":
            chat_history += f"""
<chat_history>
{st.session_state.persona_chat_history}
</chat_history>
"""

    # Conditionally build the <email> section
    if st.session_state.uploaded_emails:
        email_content = f"""
<email>
{st.session_state.uploaded_emails}
</email>
"""
    else:
        # Default email template if no uploaded emails
        email_content = """
<email>
Hi Samuel,

I recently read your article on ABC News, which prompted me to get in touch.

As you mentioned, rising inflation, energy costs, and market pressures have necessitated cost-cutting measures to maintain competitiveness. This approach is similar to what we're hearing from other telcos that are pursuing sustainable business models and aiming to deliver reasonable returns to shareholders.

We are working with AT&T, One NZ and Spark NZ to name a few on streamlining their operations, reducing costs, and gaining valuable insights from their data. By consolidating data from various sources onto a single platform, telcos can improve efficiency, enhance customer experiences, and drive innovation.

I'd be keen to speak with you about how we might be able to optimize Telstra's data infrastructure, enabling you to make data-driven decisions and unlock new revenue streams. 

Let me know if this is something you'd be open to discussing. I'll aim to follow up with a quick call over the next few days if I don't hear back from you.
</email>
"""

    # Conditionally build the <story> section
    if st.session_state.selected_customer_stories_docs:
        for story in st.session_state.selected_customer_stories_docs:
            story_content += f"""
<story>
{story}
</story>
"""

    # Construct the final prompt
    user_prompt = f"""
[INST]
{chat_history}
<profile>
{profile}
</profile>
{email_content}
{story_content}
[/INST]
Answer:
""".strip()

    # Return the prompt in the expected format
    prompt = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    return prompt

def find_stories():
    if st.session_state.customer_stories_search and st.session_state.customer_stories_filter and st.session_state.customer_stories_limit:
        results, search_column = query_stories_cortex_search_service(st.session_state.customer_stories_search, st.session_state.customer_stories_filter, st.session_state.customer_stories_limit)
        context_str = ""
        for i, r in enumerate(results, start=1):
            context_str += f"Context document {i}: {r[search_column]} \n" + "\n"
            st.session_state.customer_stories_docs.append(r[search_column])

    elif st.session_state.customer_stories_search and st.session_state.customer_stories_limit:
        results, search_column = query_stories_cortex_search_service(st.session_state.customer_stories_search, None, st.session_state.customer_stories_limit)
        context_str = ""
        for i, r in enumerate(results, start=1):
            context_str += f"Context document {i}: {r[search_column]} \n" + "\n"
            st.session_state.customer_stories_docs.append(r[search_column])