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

        # New Graph: Activity Distribution by Category
        st.write("**1. Activity Distribution by Category:**")
        activity_categories = df['Description'].apply(categorize_activity)
        category_counts = activity_categories.value_counts()

        fig, ax = plt.subplots()
        category_counts.plot(kind='bar', ax=ax)
        ax.set_title("Activity Distribution by Category")
        ax.set_xlabel("Category")
        ax.set_ylabel("Number of Activities")
        st.pyplot(fig)

        # 2. User Activity Heatmap
        st.write("**2. User Activity Heatmap:**")
        df['DayOfWeek'] = df['Time'].dt.day_name()
        df['Hour'] = df['Time'].dt.hour
        heatmap_data = df.pivot_table(index='DayOfWeek', columns='Hour', values='Description', aggfunc='count').fillna(0)

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

    else:
        st.warning("No filtered data available. Please apply filters on the Parameter Selection screen.")

    # Graph: Users with the Most Actions
    st.write("**3. Users with the Most Actions:**")
    top_users_actions = df['User'].value_counts().head(10)

    fig, ax = plt.subplots()
    top_users_actions.plot(kind='barh', ax=ax)
    ax.set_title("Top Users by Number of Actions")
    ax.set_xlabel("Number of Actions")
    ax.set_ylabel("User")
    st.pyplot(fig)

    # Graph: Actions Per Day
    st.write("**Number of Actions Per Day:**")
    actions_per_day = df.groupby(df['Time'].dt.date)['Description'].count()

    fig, ax = plt.subplots()
    actions_per_day.plot(kind='line', ax=ax)
    ax.set_title("Number of Actions Per Day")
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Actions")

    # Rotate x-axis labels to avoid overlap
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    st.pyplot(fig)

    # Graph: Activity Type Distribution Over Time
    st.write("**Activity Type Distribution Over Time:**")
    df['ActivityType'] = df['Description'].apply(categorize_activity)
    activity_type_over_time = df.groupby([df['Time'].dt.date, 'ActivityType']).size().unstack(fill_value=0)

    fig, ax = plt.subplots()
    activity_type_over_time.plot(kind='area', stacked=True, ax=ax)
    ax.set_title("Activity Type Distribution Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Actions")

    # Rotate x-axis labels to avoid overlap
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    st.pyplot(fig)

    # Graph: Top Tabs Used
    st.write("**6. Top Tabs Used:**")
    top_tabs = df['Tab'].value_counts().head(10)

    fig, ax = plt.subplots()
    top_tabs.plot(kind='bar', ax=ax)
    ax.set_title("Top Tabs Used")
    ax.set_xlabel("Tab")
    ax.set_ylabel("Number of Times Accessed")
    st.pyplot(fig)

    # Graph: Heatmap of Actions by Hour and Day
    st.write("**7. Heatmap of Actions by Hour of Day and Day of Week:**")
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



def customizable_dashboard():
    # Check if JSON data is available
    if 'json_data' not in st.session_state or st.session_state['json_data'] is None:
        st.error("No file uploaded. Please upload a JSON file on the Admin page.")
        return

    st.sidebar.title("Dashboard Customization")

    # Convert list to DataFrame if necessary
    data = pd.DataFrame(st.session_state['json_data'])

    # Ensure that the Time column is parsed as datetime
    data['Time'] = pd.to_datetime(data['Time'], errors='coerce')

    # Determine the minimum and maximum dates available in the data
    min_date = data['Time'].min().date() if not data['Time'].isna().all() else date(2000, 1, 1)
    max_date = data['Time'].max().date() if not data['Time'].isna().all() else date.today()

    # Allow users to select any date range
    selected_dates = st.sidebar.date_input("Select Date Range", [min_date, max_date])

    # Ensure the selected date range is valid
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
        if start_date > end_date:
            st.error("End date must be greater than or equal to the start date.")
            return
    else:
        st.error("Please select both a start date and an end date.")
        return

    # Button to apply the date range
    if st.sidebar.button("Apply Date Range"):
        # Store the filtered data in session state
        st.session_state['filtered_data'] = data[(data['Time'] >= pd.to_datetime(start_date)) & (data['Time'] <= pd.to_datetime(end_date))]

    # Check if the filtered data exists in session state
    if 'filtered_data' in st.session_state:
        filtered_data = st.session_state['filtered_data']

        # Notify the user if no data is available for the selected date range
        if filtered_data.empty:
            st.warning("No data available for the selected date range.")
            return

        # Widgets to customize dashboard layout
        show_activity_category = st.sidebar.checkbox("Show Activity Distribution by Category", True)
        show_user_activity_heatmap = st.sidebar.checkbox("Show User Activity Heatmap", True)
        show_top_users = st.sidebar.checkbox("Show Users with the Most Actions", True)
        show_actions_per_day = st.sidebar.checkbox("Show Number of Actions Per Day", True)
        show_activity_over_time = st.sidebar.checkbox("Show Activity Type Distribution Over Time", True)
        show_top_tabs = st.sidebar.checkbox("Show Top Tabs Used", True)

        # Displaying selected charts based on user choice
        if show_activity_category:
            filtered_data['ActivityType'] = filtered_data['Description'].apply(categorize_activity)
            category_counts = filtered_data['ActivityType'].value_counts()
            st.bar_chart(category_counts)

        if show_user_activity_heatmap:
            filtered_data['DayOfWeek'] = filtered_data['Time'].dt.day_name()
            filtered_data['Hour'] = filtered_data['Time'].dt.hour
            heatmap_data = filtered_data.pivot_table(index='DayOfWeek', columns='Hour', values='Description', aggfunc='count').fillna(0)

            if heatmap_data.empty:
                st.warning("No data available to generate the heatmap.")
            else:
                plt.figure(figsize=(10, 8))
                sns.heatmap(heatmap_data, cmap='YlGnBu', annot=True, fmt='.0f')
                plt.title('User Activity Heatmap by Day and Hour')
                plt.xlabel('Hour of Day')
                plt.ylabel('Day of Week')
                st.pyplot(plt)

        if show_top_users:
            top_users_actions = filtered_data['User'].value_counts().head(10)
            st.bar_chart(top_users_actions)

        if show_actions_per_day:
            actions_per_day = filtered_data.groupby(filtered_data['Time'].dt.date)['Description'].count()
            st.line_chart(actions_per_day)

        if show_activity_over_time:
            activity_type_over_time = filtered_data.groupby([filtered_data['Time'].dt.date, 'ActivityType']).size().unstack(fill_value=0)
            st.area_chart(activity_type_over_time)

        if show_top_tabs:
            top_tabs = filtered_data['Tab'].value_counts().head(10)
            st.bar_chart(top_tabs)


# Main functio n to define screen routing
def main():
    st.sidebar.title("Navigation")
    screen = st.sidebar.radio("Go to", ["Admin", "Chatbot", "Parameter Selection", "Parameters Results", "Interesting Statistics", "Customizable Dashboard"], index=0)

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
    elif screen == "Customizable Dashboard":
        customizable_dashboard()

if __name__ == "__main__":
    main()

