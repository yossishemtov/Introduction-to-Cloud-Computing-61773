from re import T
import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime, date
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import nltk
from nltk.chat.util import Chat, reflections
import requests
from collections import Counter

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('wordnet')

# Fetch data from Firebase
firebase_url = 'https://hw02-fe51f-default-rtdb.europe-west1.firebasedatabase.app/.json'
response = requests.get(firebase_url)
data = response.json()

# Check the structure of the data and extract the list of activities
if isinstance(data, dict):
    for key in data.keys():
        if isinstance(data[key], list):
            data = data[key]
            break
    else:
        data = None

if data is None:
    st.error("Unexpected data structure from Firebase")
    users = Counter()
    documents = Counter()
    tabs = Counter()
    descriptions = Counter()
    activities = Counter()
    total_actions = 0
    unique_users = 0
    unique_documents = 0
    unique_tabs = 0
else:
    # Process the data
    users = Counter([item.get('User', 'Unknown') for item in data])
    documents = Counter([item.get('Document', 'Unknown') for item in data])
    tabs = Counter([item.get('Tab', 'Unknown') for item in data])
    descriptions = Counter([item.get('Description', 'Unknown') for item in data])

    # Calculate some statistics
    total_actions = len(data)
    unique_users = len(users)
    unique_documents = len(documents)
    unique_tabs = len(tabs)


    # Categorize activities
    def categorize_activity(description):
        creative_keywords = ['create', 'modify', 'delete', 'assign material', 'insert', 'comment', 'rename']
        viewing_keywords = ['open', 'close', 'view']
        administrative_keywords = ['import', 'export', 'transfer', 'copy']

        if any(keyword in description.lower() for keyword in creative_keywords):
            return 'Creative'
        elif any(keyword in description.lower() for keyword in viewing_keywords):
            return 'Viewing'
        elif any(keyword in description.lower() for keyword in administrative_keywords):
            return 'Administrative'
        else:
            return 'Other'


    activities = Counter([categorize_activity(item.get('Description', '')) for item in data])

# Define patterns and responses
patterns = [
    (r'hi|hello|hey', ['Hello!', 'Hi there!', 'Welcome to the project management assistant.']),
    (r'how are you?',
     ['I\'m functioning well, thank you!', 'I\'m operational and ready to assist with your project management.']),
    (r'what is your name?', ['I\'m the Project Management Assistant.', 'You can call me the Assistant.']),
    (r'what are the main activities of the student?', [
        f"The main activities are: {activities['Creative']} creative actions, {activities['Viewing']} viewing actions, and {activities['Administrative']} administrative actions."
    ]),
    (r'are they creative?', [f"Yes, the student has performed {activities['Creative']} creative actions."]),
    (r'are they viewing?', [f"Yes, the student has performed {activities['Viewing']} viewing actions."]),
    (r'are they administrative?',
     [f"Yes, the student has performed {activities['Administrative']} administrative actions."]),
    (r'how many creative actions?', [f"The student has performed {activities['Creative']} creative actions."]),
    (r'how many viewing actions?', [f"The student has performed {activities['Viewing']} viewing actions."]),
    (r'how many administrative actions?',
     [f"The student has performed {activities['Administrative']} administrative actions."]),
    (r'exit|bye|goodbye', ['Thank you for using the Project Management Assistant. Goodbye!',
                           'Farewell! Don\'t hesitate to return if you need more assistance with your project.']),
    (r'what documents were accessed?', [f"The documents accessed were: {', '.join(documents.keys())}"]),
    (r'what tabs were used?', [f"The tabs used were: {', '.join(tabs.keys())}"]),
    (r'how many times was the document opened?', [f"The document was opened {descriptions['Open document']} times."]),
    (r'how many times was the document closed?', [f"The document was closed {descriptions['Close document']} times."]),
    (r'how many comments were made?', [f"{descriptions['Comment on a Document']} comments were made."]),
    (r'how many users interacted with the document?', [f"{unique_users} unique users interacted with the document."]),
]

# Create a chatbot
chatbot = Chat(patterns, reflections)

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []


# Function to display chat history
def display_chat_history():
    for message in st.session_state['chat_history']:
        st.write(message)


# Helper functions to load and display JSON
def load_json(file):
    try:
        json_data = json.load(file)
        return json_data
    except Exception as e:
        st.error(f"Error loading JSON: {e}")
        return None


def display_json(data):
    st.json(data)


def filter_json_data(json_data, filters, start_date=None, end_date=None):
    filtered_data = []
    if not filters and not start_date and not end_date:
        return json_data
    for item in json_data:
        match = True
        for key, value in filters.items():
            if key in item:
                item_value = str(item[key])
                if value.lower() not in item_value.lower():  # Substring match
                    match = False
                    break
        if start_date and end_date:
            item_date = item.get('Time')
            if item_date:
                item_date = datetime.strptime(item_date, '%Y-%m-%d %H:%M:%S')
                if not (start_date <= item_date.date() <= end_date):
                    match = False
        if match:
            filtered_data.append(item)
    return filtered_data


# Admin Screen to upload JSON file
def admin_screen():
    st.title("Admin Screen")
    uploaded_file = st.file_uploader("Upload JSON File", type="json")
    if uploaded_file is not None:
        json_data = load_json(uploaded_file)
        if json_data is not None:
            st.session_state['json_data'] = json_data
            st.success("File uploaded successfully!")


# Parameter Selection Screen to select parameters and apply filters
def parameter_selection_screen():
    st.title("Parameter Selection Screen")
    json_data = st.session_state.get('json_data')
    if json_data:
        st.write("Available parameters:")
        params = list(json_data[0].keys()) if isinstance(json_data, list) else list(json_data.keys())
        selected_params = st.multiselect("Select parameters", params)
        filters = {}
        for param in selected_params:
            filter_value = st.text_input(f"Filter by {param}")
            if filter_value:
                filters[param] = filter_value

        max_date = date.today()
        start_date = st.date_input("Start Date", value=max_date, max_value=max_date)
        end_date = st.date_input("End Date", value=max_date, min_value=start_date, max_value=max_date)

        st.session_state['filters'] = filters
        st.session_state['start_date'] = start_date
        st.session_state['end_date'] = end_date

        st.write(f"Selected parameters: {selected_params}")
        st.write(f"Filter values: {filters}")

        if selected_params or (start_date and end_date):
            filtered_data = filter_json_data(json_data, filters, start_date, end_date)
            st.session_state['filtered_data'] = filtered_data
            if filtered_data:
                st.success(
                    "Filters applied successfully! You can view the filtered data in the Parameters Results page.")
            else:
                st.warning("No data matches the selected filters.")
        else:
            st.warning("No filters applied. Please select parameters or specify a date range.")
    else:
        st.warning("No JSON data available. Please upload a JSON file on the Admin page.")


# Parameters Results Screen to display filtered data
def parameters_results_screen():
    st.title("Parameters Results Screen")
    filtered_data = st.session_state.get('filtered_data')
    if filtered_data:
        df = pd.DataFrame(filtered_data)
        st.table(df)
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False, header=True)
        towrite.seek(0)
        b64 = base64.b64encode(towrite.read()).decode()
        linko = f'<a href="data:application/octet-stream;base64,{b64}" download="filtered_data.xlsx"><button>Download Excel file</button></a>'
        st.markdown(linko, unsafe_allow_html=True)
    else:
        st.warning("No filtered data available. Please apply filters on the Parameter Selection screen.")


# Interesting Statistics Screen to display various statistics
def interesting_statistics_screen():
    st.title("Interesting Statistics Page")
    filtered_data = st.session_state.get('filtered_data')
    if filtered_data:
        st.write("**Filters Applied:**")
        filters = st.session_state.get('filters', {})
        for key, value in filters.items():
            st.write(f"{key}: {value}")
        st.write("---")

        df = pd.DataFrame(filtered_data)
        df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
        df = df.dropna(subset=['Time'])

        # 1. Activity Distribution by Description
        st.write("**1. Activity Distribution by Description:**")
        description_counts = df['Description'].value_counts().head(10)  # Top 10 activities
        st.bar_chart(description_counts)

        # 2. Document Interaction Patterns
        st.write("**2. Document Interaction Patterns:**")
        document_counts = df['Document'].value_counts()
        st.bar_chart(document_counts)

        # 3. User Activity Heatmap
        st.write("**3. User Activity Heatmap:**")
        df['DayOfWeek'] = df['Time'].dt.day_name()
        df['Hour'] = df['Time'].dt.hour
        heatmap_data = df.pivot_table(index='DayOfWeek', columns='Hour', values='Description', aggfunc='count').fillna(
            0)

        plt.figure(figsize=(10, 8))
        sns.heatmap(heatmap_data, cmap='YlGnBu', annot=True, fmt='.0f')
        plt.title('User Activity Heatmap by Day and Hour')
        plt.xlabel('Hour of Day')
        plt.ylabel('Day of Week')

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        st.image(buffer, caption='User Activity Heatmap')
        plt.close()

        # 4. Top Documents and Users
        st.write("**4. Top Documents and Users:**")
        top_documents = df['Document'].value_counts().head(10)
        top_users = df['User'].value_counts().head(10)

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Top Documents:**")
            st.bar_chart(top_documents)
        with col2:
            st.write("**Top Users:**")
            st.bar_chart(top_users)
    else:
        st.warning("No filtered data available. Please apply filters on the Parameter Selection screen.")


# Main function to define the screen routing
def main():
    st.sidebar.title("Navigation")
    screen = st.sidebar.radio("Go to", ["Admin", "Chatbot", "Parameter Selection", "Parameters Results",
                                        "Interesting Statistics"], index=0)

    if screen == "Admin":
        admin_screen()
    elif screen == "Chatbot":
        if 'json_data' not in st.session_state:
            st.warning("Please upload a JSON file on the Admin page before accessing the Chatbot.")
        else:
            st.write("Hello! I'm the Project Management Assistant. How can I help you today?")

            # Predefined questions
            questions = [
                "What are the main activities of the student?",
                "Are they creative?",
                "Are they viewing?",
                "Are they administrative?",
                "How many creative actions?",
                "How many viewing actions?",
                "How many administrative actions?",
                "What documents were accessed?",
                "What tabs were used?",
                "How many times was the document opened?",
                "How many times was the document closed?",
                "How many comments were made?",
                "How many users interacted with the document?"
            ]

            selected_question = st.selectbox("Select a question", questions)

            if st.button("Ask"):
                response = chatbot.respond(selected_question)
                st.session_state.chat_history.append(f"You: {selected_question}")
                st.session_state.chat_history.append(f"ChatBot: {response}")
                display_chat_history()

            user_input = st.text_input("Or type your question:", key="input")
            if user_input:
                if user_input.lower() in ['exit', 'bye', 'goodbye']:
                    st.write("ChatBot: Thank you for using the Project Management Assistant. Goodbye!")
                else:
                    response = chatbot.respond(user_input)
                    st.session_state.chat_history.append(f"You: {user_input}")
                    st.session_state.chat_history.append(f"ChatBot: {response}")
                    display_chat_history()
    elif screen == "Parameter Selection":
        parameter_selection_screen()
    elif screen == "Parameters Results":
        parameters_results_screen()
    elif screen == "Interesting Statistics":
        interesting_statistics_screen()


if __name__ == "__main__":
    main()
