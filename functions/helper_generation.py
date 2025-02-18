import streamlit as st
from functions.helper_global import *

def init_config_options_generation():
    st.session_state.selected_cortex_search_service = "LINKEDIN_SERVICE"

    with st.sidebar.expander("LLM Advanced Options"):
        st.toggle("Use chat history", key="use_chat_history", value=True)
        st.selectbox(
            "Select LLM Model",
            ("llama3.1-70b", "mistral-large2"),
            key="selected_model", help="*It is recommended to choose llama3.1-70*"
        )
        st.slider(
        "Select number of messages to use in chat history",
        value=5,
        key="num_chat_messages",
        min_value=1,
        max_value=10,
        help="*Limits the number of chats for the LLM to consider as context during a conversation.*"
    )
        st.slider(
            "Temperature/Creativity",
            value=0.5,
            key="temperature",
            step=0.1,
            min_value=0.0,
            max_value=1.0,
            help=f"""*Higher temperature will result in more creative, diverse, but potentially less coherent outputs. Conversely, lower temperature makes the model more predictable, conservative, and focused. 
Changing the temperature affects how likely the model is to select less probable tokens during text generation. 
Temperature is a scaling factor applied to the predicted probabilities of tokens. A temperature of 1 leaves the probabilities unchanged, while a temperature below 1 sharpens the distribution, making the most probable tokens even more likely to be selected.*""")
        
        st.slider(
            "Top_p/Creativity",
            value=0.8,
            key="top_p",
            step=0.1,
            min_value=0.0,
            max_value=1.0,
            help=f"""*Higher Top_p will result in a wider range of words considered, leading to more varied results. Conversely lower top_p leads to a narrower range of words considered, focusing on the most likely options. 
Changing the top_p affects affects the range of tokens the model can select from during text generation.
When top_p is 1, the model considers all possible tokens. As you decrease the top_p value, only the most probable tokens that together make up the top p% of the probability mass are included, while the rest are discarded.*"""
        )

        if st.session_state.general_chat_history != "":
            with st.container(height=150):
                st.write("Chat history summary")
                st.markdown(st.session_state.general_chat_history)

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