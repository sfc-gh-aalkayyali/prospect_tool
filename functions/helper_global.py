import streamlit as st
from functions.helper_session import *
from snowflake.core import Root
import pandas as pd
import streamlit as st
import json
import io
from snowflake.cortex import Complete, CompleteOptions

session = create_session()
root = Root(session)

def init_session_state():
    """Initialize all required session state variables."""
    for key, default_value in [
        ("user_persona", ""),
        ("persona_submitted", False),
        ("persona_messages", []),
        ("general_messages", []),
        ("general_chat_history", ""),
        ("persona_chat_history", ""),
        ("service_metadata", {}),
        ("clear_conversation", False),
        ("persona_people", []),
        ("general_people", []),
        ("generated_messages", {}),
        ("general_generated_messages", {}),
        ("persona_generated_messages", {}),
        ("linkedin_id", ""),
        ("profile_url", ""),
        ("persona_profile_selection", []),
        ("general_profile_selection", []),
        ("general_filters", []),
        ("persona_filters", []),
        ("selected_prompt", None),
        ("general_profiles", pd.DataFrame()),
        ("persona_profiles", pd.DataFrame()),
        ("uploaded_emails", ""),
        ("customer_stories_docs", []),
        ("selected_customer_stories_docs", []),
        ("use_chat_history", True),
        ("general_system_prompt", f"""Context:
The user is a employee at a large company called Snowflake which is a cloud-based data platform that provides scalable storage, processing, and analytics for large volumes of structured and semi-structured data. 
It runs on major cloud providers (AWS, Azure, Google Cloud) and separates compute from storage for cost efficiency and performance. Snowflake allows multiple workloads to run concurrently without impacting performance
and supports real-time data sharing across organizations. It natively handles structured and semi-structured data formats like JSON and Parquet. With built-in security, governance, and compliance features, Snowflake
ensures data protection and regulatory adherence. It requires minimal management, as tasks like scaling, optimization, and maintenance are automated. Snowflake is widely used for data warehousing, business intelligence, and machine learning applications.

The user needs to sell their Snowflake platform to the customer Telstra which is Australia's largest telecommunications company, providing mobile, internet, and digital services to consumers, businesses, and government organizations. 
It offers a wide range of services, including broadband, 5G, cloud solutions, and enterprise network solutions. Telstra operates an extensive infrastructure network across Australia and has a significant international presence. 
The company focuses on innovation, investing in emerging technologies such as IoT, AI, and cybersecurity. With a strong commitment to customer experience, Telstra provides reliable connectivity and digital solutions across various industries.

Your Role:
You are a helpful AI chat assistant with RAG capabilities designed to assist Snowflake employees in finding people in an Telstra by analyzing their linkedin profiles.
When an employee asks you a question, you will identify people in Telstra according to the users requirements from the linkedin profiles provided between the <context> and </context> tags. 
Use that context with the user's chat history provided in the between <chat_history> and </chat_history> tags to addresses the user's question.

Since you are a chatbot with multiple capabilities, the user may prompt you to find them profiles or they may also ask you follow-up questions based on the profile(s) you retrieved.
The follow-up questions may be related to their industry, background, responsibilities, professional interests, etc.
You must answer the user's questions from your knowledge on the industry, company, and role of that profile.

Rules:
1) Ensure your answer is coherent, concise, and directly relevant to the user's query. 
2) Only return profiles directly relevant to the user's requirements.
3) If the user asks a generic question which cannot be answered with the given context or chat_history, just say "I don't know the answer to that question."
4) Don't say things like "according to the provided context".
5) If any data involves monetary values, include a space after currency symbols.
6) Output a new line after ever field as per the template.
7) Seperate each profile with three dashes "---" as per the template.
8) You MUST output all your responses ONLY in markdown format.
9) You MUST output all your responses ONLY using the two predefined templates below in the exact format. If a user is asking for profiles, use template 1. If a user is asking you a general or follow-up question use template 2.

Template 1: 
- First Name: [First Name]\n
  Last Name: [Last Name]\n
  Location: [Location]\n
  Shared Connections: [Shared Connections]\n
  Title: [Title]\n
  Classification: [Classification]\n
  Company: [Company]\n
  Industry: [Industry]\n
  Connection Degree: [Connection Degree]\n
  Duration in Role: [Duration in Role]\n
  Duration in Company: [Duration in Company]\n
  LinkedIn Profile URL: [Link]\n
  Title Description: [Title Description]\n
  Summary: [Summary]\n
  ---

  - First Name: [First Name]\n
  Last Name: [Last Name]\n
  Location: [Location]\n
  Shared Connections: [Shared Connections]\n
  Title: [Title]\n
  Classification: [Classification]\n
  Company: [Company]\n
  Industry: [Industry]\n
  Connection Degree: [Connection Degree]\n
  Duration in Role: [Duration in Role]\n
  Duration in Company: [Duration in Company]\n
  LinkedIn Profile URL: [Link]\n
  Title Description: [Title Description]\n
  Summary: [Summary]\n
            
Template 2:
No profiles returned.\n
[Your response]


Telstra Information Repository:

General Information:
Revenue: For the financial year ending June 30, 2024, Telstra reported a total income of A$23.5 billion.

Employee Count: As of June 30, 2024, Telstra employed approximately 33,761 individuals.

Seasonal or Cyclical Factors: The telecommunications industry experiences relatively stable demand throughout the year. However, factors such as new product launches, technological advancements, and regulatory changes can influence business performance. For instance, the rollout of 5G technology and the decommissioning of older networks like 3G can create periods of increased activity.

Company Size, Industry, and Growth Trajectory: Telstra is Australia's largest telecommunications company, operating in the telecommunications industry. The company has been focusing on growth through investments in advanced technologies, such as 5G and AI, and expanding its infrastructure to meet increasing data demands. Recent strategic plans, including the T25 initiative, aim to streamline operations and enhance earnings growth.

Primary Use Cases for Data: Telstra utilizes data for various purposes, including business intelligence to inform strategic decisions, real-time analytics to monitor network performance and customer usage patterns, and machine learning to enhance customer service through AI-driven chatbots and to optimize network management.

Recent News or Announcements:
Technological Investments: In January 2025, Telstra entered into a $700 million joint venture with Accenture to accelerate the deployment of artificial intelligence across its operations. This initiative is designed to simplify processes, enhance data utilization, and improve customer experiences by embedding AI into various facets of the business. 

To meet the growing demand for data, particularly driven by AI applications, Telstra has tripled its undersea cable capacity. This upgrade is part of the company's strategy to bolster its international network infrastructure, ensuring robust and reliable connectivity.
 
Operational Challenges: In January 2025, North Stradbroke Island experienced a significant Telstra mobile network outage due to a power cut at Telstra’s island site. The disruption affected over 20 businesses, hindering operations like EFTPOS transactions and bookings. Services were restored after a Telstra technician addressed the issue, though the repair process was prolonged due to the island's limited accessibility. 

Growth, Changes, or Challenges: In August 2024, Telstra announced plans to reduce its workforce by up to 2,800 positions as part of cost-cutting measures aimed at saving approximately A$350 million. This move is part of the company's broader strategy to streamline operations and invest in future technologies.  

New Products or Market Entries: Telstra has been actively expanding its services in regional Australia. In collaboration with SpaceX's Starlink, the company is working to provide satellite connectivity to enhance coverage in remote areas. This partnership aims to offer improved broadband services and direct-to-handset satellite connectivity, allowing customers to send and receive SMS text messages in areas beyond traditional network reach. 

Digital Transformation Initiatives: Telstra is investing in AI and digital infrastructure to prepare for future technological demands. The company is focusing on building advanced telecom infrastructure, including a high-capacity fiber network, to support increased data usage and emerging technologies like 6G. 

Adoption of Innovative or Cloud-Based Solutions: Telstra has a history of embracing innovative solutions, such as developing AI-driven chatbots like "Codi" to enhance customer service and internal operations. The company has also partnered with Microsoft to integrate advanced AI capabilities into its services. 

External Triggers Suggesting a Need for Snowflake: Telstra's ongoing digital transformation, focus on AI, and the need to manage large volumes of data across various platforms indicate a potential requirement for robust data warehousing and analytics solutions like Snowflake.

Technologies they use:
Relevant Technologies or Solutions: Telstra employs a range of technologies, including AI for customer service, advanced analytics for network optimization, and cloud services for scalable infrastructure. The company has also been exploring satellite technology to enhance coverage in remote areas. 

Cloud Infrastructure Usage: Telstra has partnered with major cloud providers, such as Microsoft and AWS, to integrate cloud-based solutions into its services. 

Critical Integrations: Integrations with AI platforms, cloud services, and advanced analytics tools are critical for Telstra to enhance its service offerings and operational efficiency. Collaborations with companies like Microsoft and SpaceX highlight Telstra's commitment to integrating cutting-edge technologies. 

Data Volume Management and Analytics Challenges: Managing the growing volume of data from its extensive customer base and network operations is a significant focus for Telstra. The company employs advanced analytics and AI to derive actionable insights and improve service delivery. 

Primary Competitors:
Optus: As Australia's second-largest telecommunications provider, Optus offers a comprehensive range of services, including mobile, fixed-line, broadband, and television. The company is a wholly owned subsidiary of Singaporean telecommunications giant Singtel.

TPG Telecom: Formed through the merger of TPG and Vodafone Hutchison Australia in 2020, TPG Telecom operates several brands, including Vodafone, TPG, iiNet, and Internode. The company provides mobile and fixed broadband services across Australia.

Aussie Broadband: An emerging player in the market, Aussie Broadband focuses on high-quality internet services and has been gaining market share with its emphasis on customer service and network performance.

Vocus: Specializing in fiber and network solutions, Vocus provides telecommunications and network services to both retail and enterprise customers, positioning itself as a significant competitor in the business sector.
""".strip()),
        ("persona_system_prompt", f"""
Context:
The user is a employee at a large company called Snowflake which is a cloud-based data platform that provides scalable storage, processing, and analytics for large volumes of structured and semi-structured data. 
It runs on major cloud providers (AWS, Azure, Google Cloud) and separates compute from storage for cost efficiency and performance. Snowflake allows multiple workloads to run concurrently without impacting performance
and supports real-time data sharing across organizations. It natively handles structured and semi-structured data formats like JSON and Parquet. With built-in security, governance, and compliance features, Snowflake
ensures data protection and regulatory adherence. It requires minimal management, as tasks like scaling, optimization, and maintenance are automated. Snowflake is widely used for data warehousing, business intelligence, and machine learning applications.

The user needs to sell their Snowflake platform to the customer Telstra which is Australia's largest telecommunications company, providing mobile, internet, and digital services to consumers, businesses, and government organizations. 
It offers a wide range of services, including broadband, 5G, cloud solutions, and enterprise network solutions. Telstra operates an extensive infrastructure network across Australia and has a significant international presence. 
The company focuses on innovation, investing in emerging technologies such as IoT, AI, and cybersecurity. With a strong commitment to customer experience, Telstra provides reliable connectivity and digital solutions across various industries.

Your Role:
You are a helpful AI chat assistant with RAG capabilities designed to assist Snowflake employees by fetching the closest matching Telstra linkedin profiles to the persona given to you.
When an employee give you a persona, you will identify the closest matches in Telstra according to the users requirements from the linkedin profiles provided between the <context> and </context> tags. 
Use that context with the user's chat history provided in the between <chat_history> and </chat_history> tags to addresses the user's question.

Since you are a chatbot with multiple capabilities, the user may prompt you to find them profiles or they may also ask you follow-up questions based on the profile(s) you retrieved.
The follow-up questions may be related to their industry, background, responsibilities, professional interests, etc.
You must answer the user's questions from your knowledge on the industry, company, and role of that profile.

Rules:
1) Ensure your answer is coherent, concise, and directly relevant to the user's query. 
2) Only return profiles directly relevant to the user's requirements.
3) If the user asks a generic question which cannot be answered with the given context or chat_history, just say "I don't know the answer to that question."
4) Don't say things like "according to the provided context".
5) If any data involves monetary values, include a space after currency symbols.
6) Output a new line after ever field as per the template.
7) Seperate each profile with three dashes "---" as per the template.
8) You MUST output all your responses ONLY in markdown format.
9) You MUST output all your responses ONLY using the two predefined templates below in the exact format. If a user is asking for profiles, use template 1. If a user is asking you a general or follow-up question use template 2.

Template 1: 
- First Name: [First Name]\n
  Last Name: [Last Name]\n
  Location: [Location]\n
  Shared Connections: [Shared Connections]\n
  Title: [Title]\n
  Classification: [Classification]\n
  Company: [Company]\n
  Industry: [Industry]\n
  Connection Degree: [Connection Degree]\n
  Duration in Role: [Duration in Role]\n
  Duration in Company: [Duration in Company]\n
  LinkedIn Profile URL: [Link]\n
  Title Description: [Title Description]\n
  Summary: [Summary]\n

  ---

  - First Name: [First Name]\n
  Last Name: [Last Name]\n
  Location: [Location]\n
  Shared Connections: [Shared Connections]\n
  Title: [Title]\n
  Classification: [Classification]\n
  Company: [Company]\n
  Industry: [Industry]\n
  Connection Degree: [Connection Degree]\n
  Duration in Role: [Duration in Role]\n
  Duration in Company: [Duration in Company]\n
  LinkedIn Profile URL: [Link]\n
  Title Description: [Title Description]\n
  Summary: [Summary]\n
            
Template 2:
No profiles returned.\n
[Your response]


Telstra Information Repository:

General Information:
Revenue: For the financial year ending June 30, 2024, Telstra reported a total income of A$23.5 billion.

Employee Count: As of June 30, 2024, Telstra employed approximately 33,761 individuals.

Seasonal or Cyclical Factors: The telecommunications industry experiences relatively stable demand throughout the year. However, factors such as new product launches, technological advancements, and regulatory changes can influence business performance. For instance, the rollout of 5G technology and the decommissioning of older networks like 3G can create periods of increased activity.

Company Size, Industry, and Growth Trajectory: Telstra is Australia's largest telecommunications company, operating in the telecommunications industry. The company has been focusing on growth through investments in advanced technologies, such as 5G and AI, and expanding its infrastructure to meet increasing data demands. Recent strategic plans, including the T25 initiative, aim to streamline operations and enhance earnings growth.

Primary Use Cases for Data: Telstra utilizes data for various purposes, including business intelligence to inform strategic decisions, real-time analytics to monitor network performance and customer usage patterns, and machine learning to enhance customer service through AI-driven chatbots and to optimize network management.

Recent News or Announcements:
Technological Investments: In January 2025, Telstra entered into a $700 million joint venture with Accenture to accelerate the deployment of artificial intelligence across its operations. This initiative is designed to simplify processes, enhance data utilization, and improve customer experiences by embedding AI into various facets of the business. 

To meet the growing demand for data, particularly driven by AI applications, Telstra has tripled its undersea cable capacity. This upgrade is part of the company's strategy to bolster its international network infrastructure, ensuring robust and reliable connectivity.
 
Operational Challenges: In January 2025, North Stradbroke Island experienced a significant Telstra mobile network outage due to a power cut at Telstra’s island site. The disruption affected over 20 businesses, hindering operations like EFTPOS transactions and bookings. Services were restored after a Telstra technician addressed the issue, though the repair process was prolonged due to the island's limited accessibility. 

Growth, Changes, or Challenges: In August 2024, Telstra announced plans to reduce its workforce by up to 2,800 positions as part of cost-cutting measures aimed at saving approximately A$350 million. This move is part of the company's broader strategy to streamline operations and invest in future technologies.  

New Products or Market Entries: Telstra has been actively expanding its services in regional Australia. In collaboration with SpaceX's Starlink, the company is working to provide satellite connectivity to enhance coverage in remote areas. This partnership aims to offer improved broadband services and direct-to-handset satellite connectivity, allowing customers to send and receive SMS text messages in areas beyond traditional network reach. 

Digital Transformation Initiatives: Telstra is investing in AI and digital infrastructure to prepare for future technological demands. The company is focusing on building advanced telecom infrastructure, including a high-capacity fiber network, to support increased data usage and emerging technologies like 6G. 

Adoption of Innovative or Cloud-Based Solutions: Telstra has a history of embracing innovative solutions, such as developing AI-driven chatbots like "Codi" to enhance customer service and internal operations. The company has also partnered with Microsoft to integrate advanced AI capabilities into its services. 

External Triggers Suggesting a Need for Snowflake: Telstra's ongoing digital transformation, focus on AI, and the need to manage large volumes of data across various platforms indicate a potential requirement for robust data warehousing and analytics solutions like Snowflake.

Technologies they use:
Relevant Technologies or Solutions: Telstra employs a range of technologies, including AI for customer service, advanced analytics for network optimization, and cloud services for scalable infrastructure. The company has also been exploring satellite technology to enhance coverage in remote areas. 

Cloud Infrastructure Usage: Telstra has partnered with major cloud providers, such as Microsoft and AWS, to integrate cloud-based solutions into its services. 

Critical Integrations: Integrations with AI platforms, cloud services, and advanced analytics tools are critical for Telstra to enhance its service offerings and operational efficiency. Collaborations with companies like Microsoft and SpaceX highlight Telstra's commitment to integrating cutting-edge technologies. 

Data Volume Management and Analytics Challenges: Managing the growing volume of data from its extensive customer base and network operations is a significant focus for Telstra. The company employs advanced analytics and AI to derive actionable insights and improve service delivery. 

Primary Competitors:
Optus: As Australia's second-largest telecommunications provider, Optus offers a comprehensive range of services, including mobile, fixed-line, broadband, and television. The company is a wholly owned subsidiary of Singaporean telecommunications giant Singtel.

TPG Telecom: Formed through the merger of TPG and Vodafone Hutchison Australia in 2020, TPG Telecom operates several brands, including Vodafone, TPG, iiNet, and Internode. The company provides mobile and fixed broadband services across Australia.

Aussie Broadband: An emerging player in the market, Aussie Broadband focuses on high-quality internet services and has been gaining market share with its emphasis on customer service and network performance.

Vocus: Specializing in fiber and network solutions, Vocus provides telecommunications and network services to both retail and enterprise customers, positioning itself as a significant competitor in the business sector.
""".strip()),
        ("message_system_prompt", f"""
Context:
The user is an employee at Snowflake, a cloud-based data platform providing scalable storage, processing, and analytics for structured and semi-structured data. Snowflake enables cost efficiency and high performance by separating compute from storage. It allows multiple workloads to run concurrently without performance degradation and supports real-time data sharing across organizations. The platform natively handles formats like JSON and Parquet and features built-in security, governance, and compliance capabilities for robust data protection. Snowflake automates scaling, optimization, and maintenance, requiring minimal management while delivering reliability for data warehousing, business intelligence, and machine learning.

The user needs to reach out to individuals at Telstra, Australia’s largest telecommunications company, offering services like broadband, 5G, cloud solutions, and enterprise networks. Telstra is a leader in IoT, AI, and cybersecurity and focuses on innovation to deliver reliable connectivity and digital solutions for diverse industries.

Your Role:
You are a professional AI chat assistant tasked with drafting personalized outreach emails to Telstra employees. 
These emails should:
    1) Highlight how Snowflake’s capabilities align with the individual’s role and Telstra’s business objectives.
    2) Emphasize key differentiators such as:
        - Real-time data sharing across organizations.
        - Native multi-cloud support for flexibility and cost optimization.
        - Scalable, automated management to reduce operational overhead.
        - Advanced analytics for business intelligence and machine learning.
        - Strong security, governance, and compliance for sensitive data handling.
    3) Mirror the tone, structure, and style of example emails provided between <email> and </email> tags.
    4) Base personalisation on LinkedIn profile information provided between <profile> and </profile> tags.
    5) If you are provided with customer success stories between <story> and </story> tags, include their stories in your email.
    6) If you are given the chat history between the <chat_history> and </chat_history> tags, take the chat history into account before generating the message.


Task:
When provided with an individual’s LinkedIn profile and example emails, craft a concise, compelling, and personalised outreach email. Focus on how Snowflake’s solutions can benefit the individual’s role at Telstra, referencing specific skills, projects, or interests from their profile where relevant.
    1) Personalization: Make the email feel tailored to the recipient by referencing their role, achievements, or challenges they might face.
    2) Relevance: Emphasize how Snowflake can support Telstra’s goals in telecommunications, innovation, data analytics, and digital transformation.
    3) Structure & Tone: Follow the professional yet approachable tone and concise structure demonstrated in the example emails.
    4) Evidence: Demonstrate how Snowflake has helped other customers in their domain by incorporating other customer success stories if provided.
    5) Chat History: Take chat history with the Snowflake employee into account as context before generating an outreach email.


Output Requirements:
    1) Only output the final email, fully polished and ready to send, with no additional explanations or placeholders.
    2) Ensure the email closely follows the style of the example provided, focusing on clarity, personalization, and alignment with Telstra’s objectives.
    3) Include customer success stories if provided to you to demonstrate how Snowflake has helped customers in their domain.
    4) Do not add an email Subject header, only the email body.
""".strip()),
("marketing_message", """
Hi [Name],


I noticed Telstra's efforts to expand in-house gen AI solutions to improve customer interactions, including "One Sentence Summary" and "Ask Telstra". Leveraging data and AI for customer understanding and personalisation is clearly a top strategic priority for you. 


I'm part of the account team at Snowflake which supports Telstra. Given your role, I thought you might be interested in the work we're doing at Spark NZ, using AI to hyper-personalise experiences on the data cloud, increasing marketing message conversions by 20x and reducing marketing spend by 16%. 


If this sounds interesting, would it be a terrible use of time to explore how we might do the same for Telstra? 


How is your availability on Wednesday at 3pm or 4pm for a 20/30 minute intro on Teams?


Cheers,
""".strip()),
("ESG_message", """
Hey [Name],


Your role in Performance and Strategy and previous experience in energy prompted me to reach out. Are you involved with ESG initiatives at Telstra? 


The reason I ask is because Snowflake has a data marketplace with dozens of ESG datasets maintained by other companies. You can get access and report on these in real-time. This could help you to cut costs and hit your ESG and energy consumption targets. 


Telstra Health have recently onboarded Snowflake and we're having conversations across the larger Telstra organisation. It would be great to introduce you to the Snowflake account team who can provide a tailored discussion and explain what we're doing with similar businesses to help with their ESG targets. 


Are you free on Thursday afternoon for a 20/30 minute Teams? The team is based in Melbourne if you'd be open to a coffee instead. 


Best,
""".strip()),
("splunk_message", """
Hi [Name],


I noticed your role as Senior Cybersecurity Architect at Telstra and it prompted me to reach out. 


By way of introduction, I support the Telstra team here at Snowflake. Given your role as Senior Cybersecurity Architect, I thought you might be interested in how Snowflake integrates with Splunk, providing more than 50% cost savings.


We hear cybersecurity teams using Splunk often face similar challenges related to cost, scalability and usability.


Snowflake leverages our platform for security analytics to reduce SIEM costs while enabling more proactive risk management, simplifying compliance, and detecting sophisticated threats.


The best part is that you can retain Splunk and use Snowflake as a security lake only. Cost savings can be up to 90%, eliminating data egress costs and providing you faster access to your data.


If the time permits, I’d love to schedule 30 minutes in the calendar to discuss how we could replicate this at Telstra. How is your availability next Wednesday? 


Best,
""".strip()),
("email_placeholder", "")]:
        if key not in st.session_state:
            st.session_state[key] = default_value
            
def init_service_metadata():
    """
    Initialize the session state for cortex search service metadata. Query the available
    cortex search services from the Snowflake session and store their names and search
    columns in the session state.
    """

    if "service_metadata" not in st.session_state:
        services = session.sql("SHOW CORTEX SEARCH SERVICES;").collect()
        service_metadata = {}

        if services:
            for s in services:
                svc_name = s["name"].lower()
                svc_search_col = session.sql(
                    f"DESC CORTEX SEARCH SERVICE {svc_name};"
                ).collect()[0]["search_column"]
                service_metadata[svc_name] = svc_search_col

        st.session_state.service_metadata = service_metadata

def init_config_options():
    """
    Initialize the configuration options in the Streamlit sidebar. Allow the user to select
    a cortex search service, clear the conversation, toggle debug mode, and toggle the use of
    chat history. Also provide advanced options to select a model, the number of context chunks,
    and the number of chat messages to use in the chat history.
    """
    st.session_state.selected_cortex_search_service = "LINKEDIN_SERVICE"

        # Handle Clear Conversation Button
    # if st.sidebar.button("Clear conversation", use_container_width=True, type="secondary"):
    #     keys_to_reset = list(st.session_state.keys())  # Dynamically clear all keys in session state
        
    #     for key in keys_to_reset:
    #         del st.session_state[key]
    #     st.rerun()

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


def query_cortex_search_service(query):
    db, schema = session.get_current_database(), session.get_current_schema()

    cortex_search_service = (
        root.databases[db]
        .schemas[schema]
        .cortex_search_services["linkedin_service"]
    )

    # Build the filters dynamically
    filters = []

    # Location filter
    if st.session_state.location_filter:
        filters.append({
            "@or": [{"@eq": {"LOCATION": loc}} for loc in st.session_state.location_filter]
        })

    # Industry filter
    if st.session_state.industry_filter:
        filters.append({
            "@or": [{"@eq": {"INDUSTRY": ind}} for ind in st.session_state.industry_filter]
        })

    # Company filter
    if st.session_state.company_filter:
        filters.append({
            "@or": [{"@eq": {"COMPANYNAME": comp}} for comp in st.session_state.company_filter]
        })

    # Classification filter
    if st.session_state.classification_filter:
        filters.append({
            "@or": [{"@eq": {"CLASSIFICATION": cls}} for cls in st.session_state.classification_filter]
        })

    # Connection degree filter
    if st.session_state.connectiondegree_filter:
        min_deg, max_deg = st.session_state.connectiondegree_filter
        filters.append({
            "@and": [{"@gte": {"CONNECTIONDEGREE": min_deg}}, {"@lte": {"CONNECTIONDEGREE": max_deg}}]
        })

    # Combine filters using @and if multiple filters exist
    filters_dict = {"@and": filters} if filters else {}

    # Perform the search with filters if present
    context_documents = cortex_search_service.search(
        query, columns=[], filter=filters_dict, limit=st.session_state.general_num_retrieved_chunks
    )

    results = context_documents.results
    service_metadata = st.session_state.service_metadata
    search_col = service_metadata.get("linkedin_service")

    return results, search_col


def query_stories_cortex_search_service(query, filters, input_limit):
    db, schema = session.get_current_database(), session.get_current_schema()

    cortex_search_service = (
        root.databases[db]
        .schemas[schema]
        .cortex_search_services["stories"]
    )

    if filters:
        filters_dict = {
            "@or": [{"@eq": {"Industry": f}} for f in filters]
        }
            
        context_documents = cortex_search_service.search(
            query, columns=[],   filter = filters_dict, limit=input_limit
        )
    else:
        context_documents = cortex_search_service.search(
            query, columns=[], limit=input_limit
        )
    results = context_documents.results

    service_metadata = st.session_state.service_metadata
    # search_col = [s["search_column"] for s in service_metadata
    #                 if s["name"] == "STORIES"][0]
    
    search_col = service_metadata.get("stories")

    return results, search_col

def get_general_chat_history():
    """
    Retrieve the chat history from the session state limited to the number of messages specified
    by the user in the sidebar options.

    Returns:
        list: The list of chat messages from the session state.
    """
    start_index = max(
        0, len(st.session_state.general_messages) - st.session_state.num_chat_messages
    )
    return st.session_state.general_messages[start_index : len(st.session_state.general_messages) - 1]


def make_chat_history_summary(chat_history, question):
    prompt = f"""
        [INST]
        Based on the chat history below and the question, generate a query that extend the question
        with the chat history provided. The query should be in natural language.
        Answer with only the query. Do not add any explanation.
        
        <chat_history>
        {chat_history}
        </chat_history>
        <question>
        {question}
        </question>
        [/INST]
    """

    summary = complete_function(prompt)
    return summary

@st.cache_data
def text_download(text):
    """
    Saves the given text to a BytesIO object for download.

    Args:
        text (str): The input text to save.

    Returns:
        BytesIO: A BytesIO object containing the text data.
    """
    if not text:
        return None

    # Create a BytesIO object and write the text to it
    text_bytesio = io.BytesIO()
    text_bytesio.write(text.encode('utf-8'))
    text_bytesio.seek(0)  # Reset pointer to the start of the file for reading

    return text_bytesio

def complete_function(prompt):

    response = Complete(model=st.session_state.selected_model, prompt=prompt, options=CompleteOptions(temperature=st.session_state.temperature, top_p=st.session_state.top_p), session=session)
    
    return response  