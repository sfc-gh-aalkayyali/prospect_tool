# Prospect Tool POC
Author: Ahmad Al-Kayyali
Email: ahmad.al-kayyali@snowflake.com
  

## Overview

This Streamlit app serves as a proof-of-concept to showcase an internal tool designed to help AE's and SDR's prospect by sending the right message, to the right person, at the right time. 

The key functionalities of this app includes searching for prospects LinkedIn profiles using a RAG that uses Cortex Search and Cortex Complete to find the most relevant profiles. Once profiles are retrieved, users can curate personalised messages, emails, scripts, etc all with the help of AI.

## Disclaimer

Please note that this guide is only to get the app up and running. However, this app will not work out of the box without access to the required data, Cortex Search instances, etc.  If you would like guidance on this please email the author for more information.

This app includes the necessary docker file for deployment on SPCS (Snowpark Container Services) however instructions for deployment are beyond the scope of this documentation as the setup can differ based on the environment and requirments for access.

Note that your use of the code in this repository is subject to the [Apache License](https://www.apache.org/licenses/LICENSE-2.0).


## Prerequisites

Before following the steps below please ensure you have a snow cli connection set up.

If you have not done this already, please navigate to the [Snowflake CLI Configuration](https://docs.snowflake.com/en/developer-guide/snowflake-cli/connecting/configure-connections#add-a-connection) page and follow the steps.

  

Once you have created a snow cli connection, please note down your connection name as you will need it for a later step.
  

## Local Setup Instructions

  

### Step 1 - Activate Conda Environment & Virtual Environment

  

 Ensure you are in your project directory:

```bash

cd path/to/project

```

Create and activate a virtual environment using python 3.10 by running:

```bash

python3.10 -m venv venv

```
If you are using macOS/Linux, run:

```bash

source venv/bin/activate

```
Alternatively, if you are using Windows, run:

```bash

venv\Scripts\activate

```


### Step 2 - Install Dependencies for Local Development

Install required dependencies:

```bash

pip install -r requirements.txt

```

  

### Step 3 - Start Streamlit App Locally

  

Test your Snowflake connection before starting the app:
*Note, if you have 2MFA this will invoke your preferred method for verification*

```bash

snow connection test --connection my_conn

```


Once the connection is successful, navigate to the "files" folder and open the `helper_session.py` file.

Modify the following line of code on **line 64**:
Replace `"my_conn"` with the actual name of your Snowflake CLI connection. To find your connection name, run:


```python

session = Session.builder.config("connection_name", "my_conn").create()

```

Start the Streamlit app by running:

```bash

streamlit run Root.py

```

Open the provided URL in your browser to interact with the app.

## Project Breakdown

### `Root.py`

Landing page and sidebar logic

### `prompts/`

Prompts used for LLM calls
  
### `functions/`

Helper files

### `files/`
  
Main logic for each page
