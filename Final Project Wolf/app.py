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

#json's firebase
firebase_history_url = 'https://hw03-16951-default-rtdb.europe-west1.firebasedatabase.app/.json'

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
    (r'how are you?', ['I\'m functioning well, thank you!', 'I\'m operational and ready to assist with your project management.']),
    (r'what is your name?', ['I\'m the Project Management Assistant.', 'You can call me the Assistant.']),
    (r'what are the main activities of the student?', [f"The main activities are: {activities['Creative']} creative actions, {activities['Viewing']} viewing actions, and {activities['Administrative']} administrative actions."]),
    (r'are they creative?', [f"Yes, the student has performed {activities['Creative']} creative actions."]),
    (r'are they viewing?', [f"Yes, the student has performed {activities['Viewing']} viewing actions."]),
    (r'are they administrative?', [f"Yes, the student has performed {activities['Administrative']} administrative actions."]),
    (r'how many creative actions?', [f"The student has performed {activities['Creative']} creative actions."]),
    (r'how many viewing actions?', [f"The student has performed {activities['Viewing']} viewing actions."]),
    (r'how many administrative actions?', [f"The student has performed {activities['Administrative']} administrative actions."]),
    (r'exit|bye|goodbye', ['Thank you for using the Project Management Assistant. Goodbye!', 'Farewell! Don\'t hesitate to return if you need more assistance with your project.']),
    (r'what documents were accessed?', [f"The documents accessed were: {', '.join(documents.keys())}"]),
    (r'what tabs were used?', [f"The tabs used were: {', '.join(tabs.keys())}"]),
    (r'how many times was the document opened?', [f"The document was opened {descriptions['Open document']} times."]),
    (r'how many times was the document closed?', [f"The document was closed {descriptions['Close document']} times."]),
    (r'how many comments were made?', [f"{descriptions['Comment on a Document']} comments were made."]),
    (r'how many users interacted with the document?', [f"{unique_users} unique users interacted with the document."]),
]

# Create a chatbot
chatbot = Chat(patterns, reflections)

def initialize_chatbot(json_data):
    # Process the data to extract relevant information for the chatbot
    users = Counter([item.get('User', 'Unknown') for item in json_data])
    documents = Counter([item.get('Document', 'Unknown') for item in json_data])
    tabs = Counter([item.get('Tab', 'Unknown') for item in json_data])
    descriptions = Counter([item.get('Description', 'Unknown') for item in json_data])

    total_actions = len(json_data)
    unique_users = len(users)
    unique_documents = len(documents)
    unique_tabs = len(tabs)

    activities = Counter([categorize_activity(item.get('Description', '')) for item in json_data])

    # Define patterns and responses
    patterns = [
        (r'hi|hello|hey', ['Hello!', 'Hi there!', 'Welcome to the project management assistant.']),
        (r'how are you?', ['I\'m functioning well, thank you!', 'I\'m operational and ready to assist with your project management.']),
        (r'what is your name?', ['I\'m the Project Management Assistant.', 'You can call me the Assistant.']),
        (r'what are the main activities of the student?', [f"The main activities are: {activities['Creative']} creative actions, {activities['Viewing']} viewing actions, and {activities['Administrative']} administrative actions."]),
        (r'are they creative?', [f"Yes, the student has performed {activities['Creative']} creative actions."]),
        (r'are they viewing?', [f"Yes, the student has performed {activities['Viewing']} viewing actions."]),
        (r'are they administrative?', [f"Yes, the student has performed {activities['Administrative']} administrative actions."]),
        (r'how many creative actions?', [f"The student has performed {activities['Creative']} creative actions."]),
        (r'how many viewing actions?', [f"The student has performed {activities['Viewing']} viewing actions."]),
        (r'how many administrative actions?', [f"The student has performed {activities['Administrative']} administrative actions."]),
        (r'exit|bye|goodbye', ['Thank you for using the Project Management Assistant. Goodbye!', 'Farewell! Don\'t hesitate to return if you need more assistance with your project.']),
        (r'what documents were accessed?', [f"The documents accessed were: {', '.join(documents.keys())}"]),
        (r'what tabs were used?', [f"The tabs used were: {', '.join(tabs.keys())}"]),
        (r'how many times was the document opened?', [f"The document was opened {descriptions['Open document']} times."]),
        (r'how many times was the document closed?', [f"The document was closed {descriptions['Close document']} times."]),
        (r'how many comments were made?', [f"{descriptions['Comment on a Document']} comments were made."]),
        (r'how many users interacted with the document?', [f"{unique_users} unique users interacted with the document."]),
    ]

    # Create a chatbot
    return Chat(patterns, reflections)


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


def chatbot_screen():
    if 'json_data' not in st.session_state or not st.session_state['json_data']:
        st.warning("Please select and load a JSON file on the Admin page before accessing the Chatbot.")
        return
    
    st.write("Hello! I'm the Project Management Assistant. How can I help you today?")
    
    # Initialize the chatbot with the selected JSON data
    chatbot = initialize_chatbot(st.session_state['json_data'])

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

    # Button to ask a selected question
    if st.button("Ask"):
        response = chatbot.respond(selected_question)
        st.session_state.chat_history.append(f"You: {selected_question}")
        st.session_state.chat_history.append(f"ChatBot: {response}")

    # Text input for user to type a custom question
    user_input = st.text_input("Or type your question:", key="input")
    if user_input:
        if user_input.lower() in ['exit', 'bye', 'goodbye']:
            st.write("ChatBot: Thank you for using the Project Management Assistant. Goodbye!")
        else:
            response = chatbot.respond(user_input)
            st.session_state.chat_history.append(f"You: {user_input}")
            st.session_state.chat_history.append(f"ChatBot: {response}")

    # Button to clear chat history
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.success("Chat history cleared!")

    # Display chat history at the end
    display_chat_history()




# Admin Screen to upload JSON file and show history of uploads
def admin_screen():
    st.title("Admin Screen")

    # Retrieve the upload history from Firebase
    response = requests.get(firebase_history_url)
    if response.status_code == 200 and response.json():
        st.session_state['upload_history'] = response.json()
    else:
        st.session_state['upload_history'] = []

    # Upload a new JSON file
    uploaded_file = st.file_uploader("Upload JSON File", type="json")

    if uploaded_file is not None:
        # Load and store the JSON data
        json_data = load_json(uploaded_file)
        if json_data is not None:
            # Check if the uploaded file already exists in the upload history
            if not any(record['filename'] == uploaded_file.name for record in st.session_state['upload_history']):
                # Create a new entry for the upload history
                new_entry = {
                    "filename": uploaded_file.name,
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "data": json_data
                }

                # Add the new entry to the history
                st.session_state['upload_history'].append(new_entry)

                # Update the history in Firebase
                response = requests.put(firebase_history_url, json.dumps(st.session_state['upload_history']))
                if response.status_code == 200:
                    st.success(f"File '{uploaded_file.name}' uploaded successfully!")
                else:
                    st.error("Failed to update the upload history in Firebase.")
            else:
                st.warning("This file has already been uploaded.")

    # Dropdown to select a JSON file from upload history
    st.subheader("Select a JSON File")
    if st.session_state['upload_history']:
        file_options = [record['filename'] for record in st.session_state['upload_history']]
        selected_file = st.selectbox("Choose a JSON file", file_options)

        if selected_file:
            # Only load the selected JSON data if it's not already loaded
            if 'selected_file' not in st.session_state or st.session_state['selected_file'] != selected_file:
                # Find the selected JSON data
                for record in st.session_state['upload_history']:
                    if record['filename'] == selected_file:
                        selected_data = record['data']
                        st.session_state['json_data'] = selected_data
                        st.session_state['selected_file'] = selected_file
                        st.success(f"JSON data from '{selected_file}' loaded successfully!")
                        break
    else:
        st.write("No files available for selection.")

        
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
                st.success("Filters applied successfully! You can view the filtered data in the Parameters Results page.")
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

        # Prepare the Excel file download button
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False, header=True)
        towrite.seek(0)
        b64 = base64.b64encode(towrite.read()).decode()
        linko = f'<a href="data:application/octet-stream;base64,{b64}" download="filtered_data.xlsx"><button>Download Excel file</button></a>'
        
        # Display the download button above the table
        st.markdown(linko, unsafe_allow_html=True)
        
        # Display the table
        st.table(df)
    else:
        st.warning("No filtered data available. Please apply filters on the Parameter Selection screen.")


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

        # Dropdown menu to select graphs
        graphs_to_display = st.multiselect(
            "Select graphs to display",
            ["Activity Distribution by Category",
             "Users with the Most Actions",
             "Number of Actions Per Day",
             "Activity Type Distribution Over Time",
             "Top Tabs Used",
             "Heatmap of Actions by Hour of Day and Day of Week",  # Keep only this heatmap
             "Activities Distribution Among Students"],  # New graph option
            default=["Activity Distribution by Category", "Activities Distribution Among Students"]  # Default selections
        )

        # Add logic to display each graph
        if "Activity Distribution by Category" in graphs_to_display:
            st.write("**1. Activity Distribution by Category:**")
            activity_categories = df['Description'].apply(categorize_activity)
            category_counts = activity_categories.value_counts()

            fig, ax = plt.subplots()
            category_counts.plot(kind='bar', ax=ax)
            ax.set_title("Activity Distribution by Category")
            ax.set_xlabel("Category")
            ax.set_ylabel("Number of Activities")
            st.pyplot(fig)

        if "Users with the Most Actions" in graphs_to_display:
            st.write("**2. Users with the Most Actions:**")
            top_users_actions = df['User'].value_counts().head(10)

            fig, ax = plt.subplots()
            top_users_actions.plot(kind='barh', ax=ax)
            ax.set_title("Top Users by Number of Actions")
            ax.set_xlabel("Number of Actions")
            ax.set_ylabel("User")
            st.pyplot(fig)

        if "Number of Actions Per Day" in graphs_to_display:
            st.write("**3. Number of Actions Per Day:**")
            actions_per_day = df.groupby(df['Time'].dt.date)['Description'].count()

            fig, ax = plt.subplots()
            actions_per_day.plot(kind='line', ax=ax)
            ax.set_title("Number of Actions Per Day")
            ax.set_xlabel("Date")
            ax.set_ylabel("Number of Actions")

            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            st.pyplot(fig)

        if "Activity Type Distribution Over Time" in graphs_to_display:
            st.write("**4. Activity Type Distribution Over Time:**")
            df['ActivityType'] = df['Description'].apply(categorize_activity)
            activity_type_over_time = df.groupby([df['Time'].dt.date, 'ActivityType']).size().unstack(fill_value=0)

            fig, ax = plt.subplots()
            activity_type_over_time.plot(kind='area', stacked=True, ax=ax)
            ax.set_title("Activity Type Distribution Over Time")
            ax.set_xlabel("Date")
            ax.set_ylabel("Number of Actions")

            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            st.pyplot(fig)

        if "Top Tabs Used" in graphs_to_display:
            st.write("**5. Top Tabs Used:**")
            top_tabs = df['Tab'].value_counts().head(10)

            fig, ax = plt.subplots()
            top_tabs.plot(kind='bar', ax=ax)
            ax.set_title("Top Tabs Used")
            ax.set_xlabel("Tab")
            ax.set_ylabel("Number of Times Accessed")
            st.pyplot(fig)

        if "Heatmap of Actions by Hour of Day and Day of Week" in graphs_to_display:
            st.write("**6. Heatmap of Actions by Hour of Day and Day of Week:**")
            df['DayOfWeek'] = df['Time'].dt.day_name()
            df['Hour'] = df['Time'].dt.hour
            actions_heatmap_data = df.pivot_table(index='DayOfWeek', columns='Hour', values='Description', aggfunc='count').fillna(0)

            plt.figure(figsize=(10, 8))
            sns.heatmap(actions_heatmap_data, cmap='coolwarm', annot=True, fmt='.0f')
            plt.title('Heatmap of Actions by Hour of Day and Day of Week')
            plt.xlabel('Hour of Day')
            plt.ylabel('Day of Week')

            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            st.image(buffer, caption='Heatmap of Actions by Hour of Day and Day of Week')
            plt.close()

        if "Activities Distribution Among Students" in graphs_to_display:
            st.write("**7. Activities Distribution Among Students:**")
            
            # Group by user and activity type
            student_activity = df.groupby(['User', df['Description'].apply(categorize_activity)]).size().unstack(fill_value=0)
            
            fig, ax = plt.subplots()
            student_activity.plot(kind='bar', stacked=True, ax=ax, colormap='viridis')
            ax.set_title("Activities Distribution Among Students")
            ax.set_xlabel("Student")
            ax.set_ylabel("Number of Activities")
            st.pyplot(fig)

    else:
        st.warning("No filtered data available. Please apply filters on the Parameter Selection screen.")





# Main functio n to define screen routing
def main():
    st.sidebar.title("Navigation")
    screen = st.sidebar.radio("Go to", ["Admin", "Chatbot", "Parameter Selection", "Parameters Results", "Interesting Statistics"], index=0)

    if screen == "Admin":
        admin_screen()
    elif screen == "Chatbot":
        chatbot_screen()
    elif screen == "Parameter Selection":
        parameter_selection_screen()
    elif screen == "Parameters Results":
        parameters_results_screen()
    elif screen == "Interesting Statistics":
        interesting_statistics_screen()

if __name__ == "__main__":
    main()
