import streamlit as st
from functions.helper_global import *

def init_config_options_generation():
    st.session_state.selected_cortex_search_service = "LINKEDIN_SERVICE"

    with st.sidebar.expander("LLM Advanced Options"):
        st.toggle("Use chat history", key="use_chat_history", value=True)

        # Selectbox using session state
        st.selectbox(
            "Select LLM Model",
            ("deepseek-r1", "llama3.1-70b"),
            key="selected_model"
        )

        st.slider(
            "Temperature/Creativity",
            step=0.1,
            value=st.session_state.get("temperature", 0.7),
            min_value=0.0,
            max_value=1.0,
            help=f"""*Higher temperature will result in more creative, diverse, but potentially less coherent outputs. Conversely, lower temperature makes the model more predictable, conservative, and focused. 
Changing the temperature affects how likely the model is to select less probable tokens during text generation. 
Temperature is a scaling factor applied to the predicted probabilities of tokens. A temperature of 1 leaves the probabilities unchanged, while a temperature below 1 sharpens the distribution, making the most probable tokens even more likely to be selected.*""")
        
        st.slider(
            "Top_p/Creativity",
            value=st.session_state.get("top_p", 0.9),
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

def create_direct_message(profile):
    system_prompt = st.session_state.system_prompt
    sample_message = st.session_state.sample_message

    story_content = ""

    if st.session_state.selected_customer_stories_docs:
        for story in st.session_state.selected_customer_stories_docs:
            story_content += f"""
<story>
{story}
</story>
""".strip()
    
    battle_card_content = ""

    if st.session_state.selected_battle_cards:
        for battlecard in st.session_state.selected_battle_cards:
            battle_card_content = f"""
<battlecard>
{battlecard}
</battlecard>
""".strip()

    # Construct the final prompt
    user_prompt = f"""
[INST]
<profile>
{profile}
</profile>
<example>
{sample_message}
</example>
{story_content}
{battle_card_content}
[/INST]
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