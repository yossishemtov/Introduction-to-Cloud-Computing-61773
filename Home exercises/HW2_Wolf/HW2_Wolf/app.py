import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# Helper functions to load and display JSON

# Function to load JSON file
def load_json(file):

    try:
        json_data = json.load(file)
        return json_data
    except Exception as e:
        st.error(f"Error loading JSON: {e}")
        return None

# Function to display JSON data
def display_json(data):
    st.json(data)

# Function to filter JSON data based on given filters
def filter_json_data(json_data, filters):
    filtered_data = []


    if not filters:
        return json_data


    for item in json_data:
        match = True

        for key, value in filters.items():
            if key in item:
                item_value = str(item[key])

                if is_date(value):  # If the filter value is a date
                    if not item_value.startswith(value):
                        match = False
                        break

                elif value.lower() not in item_value.lower():  # Substring match
                    match = False
                    break

        if match:
            filtered_data.append(item)
    return filtered_data

# Function to check if a string is a date
def is_date(string):

    try:
        datetime.strptime(string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

# Admin Screen to upload JSON file
def admin_screen():
    st.title("Admin Screen")
    uploaded_file = st.file_uploader("Upload JSON.txt File", type="txt")

    # Handle the Json upload mechanism
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

        # Filtering options for multiple parameters
        filters = {}
        for param in selected_params:
            filter_value = st.text_input(f"Filter by {param}")
            if filter_value:
                filters[param] = filter_value

        st.session_state['filters'] = filters
        st.write(f"Selected parameters: {selected_params}")
        st.write(f"Filter values: {filters}")

        # Directly filter the data and store it in session state
        filtered_data = filter_json_data(json_data, filters)
        st.session_state['filtered_data'] = filtered_data

        st.success("Filters applied successfully! You can view the filtered data in the Parameters Results page.")

    else:
        st.warning("No JSON data available. Please upload a JSON file on the Admin page.")

# Parameters Results Screen to display filtered data
# This part handles the data filtering feature
def parameters_results_screen():
    st.title("Parameters Results Screen")
    filtered_data = st.session_state.get('filtered_data')

    if filtered_data:
        df = pd.DataFrame(filtered_data)
        
        # CSS to adjust the width of the date column
        st.markdown(
            """
            <style>
            .dataframe tbody tr td:nth-child(1) {
                min-width: 200px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Add export button
        try:
            towrite = io.BytesIO()
            df.to_excel(towrite, index=False, header=True)
            towrite.seek(0)
            b64 = base64.b64encode(towrite.read()).decode()
            linko = f'<a href="data:application/octet-stream;base64,{b64}" download="filtered_data.xlsx"><button>Download Excel file</button></a>'
            st.markdown(linko, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error exporting to Excel: {e}")

        # Display the table
        st.table(df)
    else:
        st.warning("No filtered data available. Please apply filters on the Parameter Selection screen.")

# Interesting Statistics Screen to display various statistics
# This function handles the statistics feature
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

# Define the screen routing
def main():
    st.sidebar.title("Navigation")
    screen = st.sidebar.radio("Go to", ["Admin", "Parameter Selection", "Parameters Results", "Interesting Statistics"])

    #render the appropriate page according to radio button selection
    if screen == "Admin":
        admin_screen()
    elif screen == "Parameter Selection":
        parameter_selection_screen()
    elif screen == "Parameters Results":
        parameters_results_screen()
    elif screen == "Interesting Statistics":
        interesting_statistics_screen()

if __name__ == "__main__":
    main()
