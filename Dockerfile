# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11

# Set the working directory
WORKDIR /src

# Copy the current directory contents into the container at /app
COPY . /src

# Install the necessary packages
RUN pip install -r requirements.txt

# Expose the port that Streamlit will run on
EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "src/Root.py"]

