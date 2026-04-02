# http_server.py
import http.server
import socketserver
import urllib.parse
from datetime import datetime
import pandas as pd
import re # Import regex for parsing percentages

PORT = 8000

# Global dictionary to store user data across requests.
# In a real-world multi-user application, this would be replaced with
# a database or proper session management.
user_data = {}

# DataFrame for health parameters based on age range
df_health_parameters = pd.DataFrame({
    'range': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    'HR_U': [160, 100, 100, 100, 100, 90, 90, 90, 80, 80],
    'HR_L': [80, 60, 60, 60, 60, 60, 60, 60, 60, 60],
    'SBP': [100, 120, 120, 120, 125, 135, 145, 145, 145, 145],
    'DBP': [70, 80, 80, 80, 85, 90, 95, 95, 95, 95],
    'SpO2': [95, 95, 95, 95, 95, 95, 95, 95, 95, 95]
})

# Dictionary of diseases and their symptoms
diseases = {
    "Heart Attack": [
        "Chest Pain / Discomfort", "Body Pain", "Breathing Problem", "Cold Sweat", "Nausea", "Vomiting", "Dizziness", "Fatigue"
    ],
    "Brain Stroke": [
        "Weakness", "Numbness", "Confusion", "Trouble Understanding", "Trouble Speaking", "Vision Problem", "Headache", "Dizziness", "Balance / Coordination Loss"
    ],
    "Asthma": [
        "Wheezing", "Cough", "Breathing Problem", "Chest Pain / Discomfort", "Fatigue"
    ],
    "Panic Attack": [
        "Sudden Intense Fear / Discomfort", "Rapid Heart Beat", "Sweating", "Shivering", "Breathing Problem", "Chest Pain / Discomfort", "Nausea", "Dizziness", "Numbness", "Chills", "Fainting Feeling"
    ],
    "Hypertensive Disorder": [
        "Headache", "Chest Pain / Discomfort", "Breathing Problem", "Nose Bleeds"
    ],
    "Hypotensive Disorder": [
        "Dizziness", "Fatigue", "Vision Problem", "Nausea", "Vomiting", "Fainting Feeling"
    ],
    "Stress": [
        "Fatigue", "Muscle Tension", "Headache", "Irritation", "Emotional Unstability", "Unstable Behavior", "Concentration Problem"
    ],
    "Anxiety": [
        "Excessive Fear / Worry", "Restlessness", "Fatigue", "Muscle Tension", "Concentration Problem", "Irritation", "Unstable Behavior"
    ],
    "Pulmonary Embolism": [
        "Breathing Problem", "Chest Pain / Discomfort", "Cough", "Rapid Heart Beat", "Dizziness", "Fainting Feeling"
    ],
    "Tachycardia": [
        "Rapid Heart Beat", "Breathing Problem", "Dizziness", "Chest Pain / Discomfort"
    ],
    "Bradycardia": [
        "Fatigue", "Dizziness", "Weakness", "Fainting Feeling"
    ],
    "Arrhythmia": [
        "Heart Palpitation", "Chest Pain / Discomfort", "Breathing Problem", "Fainting Feeling"
    ],
    "Heat Stroke": [
        "Hot & Dry Skin", "Confusion", "Rapid Heart Beat", "Dizziness", "Headache", "Nausea", "Vomiting", "No Sweating", "Breathing Problem"
    ],
    "Hypothermia": [
        "Shivering", "Confusion", "Slurred Speech", "Drowsiness", "Balance / Coordination Loss", "Bluing of Lips & Fingertips"
    ],
    "Epilepsy": [
        "Shivering", "Seizures", "Fainting Feeling", "Muscle Tension", "Confusion", "Fatigue", "Concentration Problem", "Headache"
    ],
    "Heart Failure": [
        "Breathing Problem", "Fatigue", "Weakness", "Rapid Heart Beat", "Cough", "Chest Pain / Discomfort"
    ],
    "Sleep Paralysis": [
        "Intense Fear / Worry", "Hallucinations", "Inability Moving"
    ],
    "Depression": [
        "Emotional Unstability", "Unstable Behavior", "Fatigue", "Concentration Problem"
    ]
}

# Create a unique list of all symptoms
all_symptoms = list(set(symptom for symptoms in diseases.values() for symptom in symptoms))
all_symptoms.sort() # Sort for consistent display

# Function to calculate age
def calculate_age(dob_str):
    today = datetime.today()
    dob = datetime.strptime(dob_str, "%Y-%m-%d")
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age

# Function to get individual parameters based on range input
def get_parameters_from_df(input_range):
    result = df_health_parameters[df_health_parameters['range'] == input_range]
    if not result.empty:
        HR_U = result['HR_U'].values[0]
        HR_L = result['HR_L'].values[0]
        SBP = result['SBP'].values[0]
        DBP = result['DBP'].values[0]
        SpO2 = result['SpO2'].values[0]
        return HR_U, HR_L, SBP, DBP, SpO2
    else:
        return None, None, None, None, None

# HTML Template for Tron-like styling
TRON_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    body {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(45deg, #0d0d0d, #1a1a1a, #0d0d0d);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        color: #00e6e6; /* Neon blue text */
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start; /* Align to top for menu bar */
        min-height: 100vh;
        margin: 0;
        padding: 0; /* Remove padding from body */
        box-sizing: border-box;
        text-shadow: 0 0 5px #00e6e6; /* Text glow */
        overflow-x: hidden; /* Prevent horizontal scroll from gradient */
    }

    @keyframes gradientShift {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }

    .navbar {
        width: 100%;
        background-color: #0d0d0d;
        padding: 15px 0;
        border-bottom: 2px solid #00e6e6;
        box-shadow: 0 0 15px #00e6e6;
        text-align: center;
        margin-bottom: 30px; /* Space below navbar */
    }

    .navbar a {
        color: #00ffff;
        text-decoration: none;
        padding: 10px 20px;
        margin: 0 10px;
        font-size: 1.2em;
        transition: color 0.3s ease, text-shadow 0.3s ease;
    }

    .navbar a:hover {
        color: #00ff00; /* Green on hover */
        text-shadow: 0 0 10px #00ff00;
    }

    .container {
        background-color: #1a1a1a; /* Slightly lighter dark for container */
        border: 2px solid #00e6e6; /* Neon border */
        box-shadow: 0 0 20px #00e6e6; /* Container glow */
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        width: 100%;
        max-width: 600px; /* Increased max-width for better layout */
        box-sizing: border-box;
        margin-bottom: 30px; /* Space below container */
    }
    h1, h2 {
        color: #00ffff; /* Brighter neon for headings */
        text-shadow: 0 0 10px #00ffff;
        margin-bottom: 20px;
    }
    label {
        display: block;
        margin-bottom: 10px;
        font-size: 1.1em;
        color: #00e6e6;
    }
    input[type="text"],
    input[type="date"],
    input[type="number"],
    select,
    textarea { /* Added textarea for potential future use or larger text areas */
        width: calc(100% - 20px);
        padding: 10px;
        margin-bottom: 20px;
        background-color: #2a2a2a; /* Dark input background */
        border: 1px solid #00e6e6;
        color: #00e6e6;
        border-radius: 8px;
        box-shadow: inset 0 0 5px #00e6e6;
        font-size: 1em;
        outline: none;
    }
    input[type="text"]:focus,
    input[type="date"]:focus,
    input[type="number"]:focus,
    select:focus,
    textarea:focus {
        border-color: #00ffff;
        box-shadow: inset 0 0 8px #00ffff, 0 0 10px #00ffff;
    }
    button {
        position: relative;
        background-color: #00e6e6;
        color: #0d0d0d;
        padding: 12px 25px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 1.1em;
        font-weight: bold;
        transition: background-color 0.3s ease, box-shadow 0.3s ease, color 0.3s ease;
        box-shadow: 0 0 10px #00e6e6;
        overflow: hidden; /* For fluidic border effect */
        z-index: 1;
    }
    button:hover {
        background-color: #00ffff;
        color: #0d0d0d;
        box-shadow: 0 0 15px #00ffff, 0 0 25px #00ffff;
    }

    /* Fluidic border animation for buttons */
    button::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: conic-gradient(
            transparent 0deg,
            transparent 90deg,
            #00ffff 90deg,
            #00ffff 180deg,
            #00e6e6 180deg,
            #00e6e6 270deg,
            #00ff00 270deg,
            #00ff00 360deg
        );
        z-index: -1;
        animation: rotateBorder 4s linear infinite;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    button:hover::before {
        opacity: 1;
    }
    @keyframes rotateBorder {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .error {
        color: #ff3333; /* Neon red for errors */
        text-shadow: 0 0 5px #ff3333;
        margin-top: -10px;
        margin-bottom: 15px;
    }
    .message {
        color: #00ff00; /* Neon green for success messages */
        text-shadow: 0 0 5px #00ff00;
        margin-top: 15px;
    }
    .result-section {
        background-color: #1a1a1a;
        border: 1px solid #00e6e6;
        border-radius: 10px;
        padding: 15px;
        margin-top: 20px;
        text-align: left;
        box-shadow: 0 0 10px #00e6e6;
    }
    .result-section h3 {
        color: #00ffff;
        text-shadow: 0 0 8px #00ffff;
        margin-bottom: 10px;
    }
    .result-section p {
        margin-bottom: 8px;
        line-height: 1.4;
    }
    .result-section strong {
        color: #00ffff;
    }
    .checkbox-group {
        max-height: 300px;
        overflow-y: auto;
        border: 1px solid #00e6e6;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 20px;
        background-color: #2a2a2a;
        box-shadow: inset 0 0 5px #00e6e6;
    }
    .checkbox-group label {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
        font-size: 0.95em;
    }
    .checkbox-group input[type="checkbox"] {
        width: auto;
        margin-right: 10px;
        accent-color: #00e6e6; /* For checked state */
        box-shadow: none; /* Override default input shadow for checkboxes */
    }
    .button-group {
        display: flex;
        flex-wrap: wrap; /* Allow buttons to wrap */
        justify-content: center;
        gap: 15px;
        margin-top: 20px;
    }
    /* Risk colors */
    .risk-high { color: #ff3333; text-shadow: 0 0 5px #ff3333; } /* Red */
    .risk-medium { color: #ffff00; text-shadow: 0 0 5px #ffff00; } /* Yellow */
    .risk-low { color: #00ff00; text-shadow: 0 0 5px #00ff00; } /* Green */
    .risk-neutral { color: #00e6e6; } /* Default neon blue */
</style>
"""

def generate_html_page(title, body_content, error_message=None, success_message=None):
    """Generates a complete HTML page with Tron styling and a menu bar."""
    error_html = f'<p class="error">{error_message}</p>' if error_message else ''
    success_html = f'<p class="message">{success_message}</p>' if success_message else ''
    
    navbar_html = """
    <div class="navbar">
        <a href="/">Home</a>
        <a href="/start_assessment">Start Assessment</a>
        <a href="/about">About</a>
    </div>
    """

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {TRON_STYLE}
</head>
<body>
    {navbar_html}
    <div class="container">
        <h1>{title}</h1>
        {error_html}
        {success_html}
        {body_content}
    </div>
</body>
</html>
"""

def get_homepage_html():
    """HTML for the homepage."""
    body = f"""
    <p>Welcome to the Tron Health Assessment System!</p>
    <p>This application helps you assess your health status based on various physiological parameters and symptoms. It provides insights into potential health conditions, inspired by the futuristic aesthetics of Tron.</p>
    <p>Navigate through the assessment by clicking 'Start Assessment' in the menu bar.</p>
    <form action="/start_assessment" method="get">
        <button type="submit">Start Assessment</button>
    </form>
    """
    return generate_html_page("Welcome to Tron Health", body)

def get_about_html():
    """HTML for the About page."""
    body = f"""
    <p>This health assessment model is designed to provide preliminary insights based on inputted physiological data and reported symptoms. It leverages a rule-based system derived from general health guidelines and common symptom associations with various diseases.</p>
    <p><b>Disclaimer:</b> This application is for informational purposes only and does not constitute medical advice. Always consult with a qualified healthcare professional for any health concerns or before making any decisions related to your health.</p>
    <p>Developed with Python's `http.server` and styled with a Tron-inspired aesthetic.</p>
    """
    return generate_html_page("About This Model", body)


def get_name_input_html(error=None):
    """HTML for name input page."""
    body = f"""
    <form action="/submit_name" method="post">
        <label for="name">Enter Your Name:</label>
        <input type="text" id="name" name="name" required>
        <button type="submit">Proceed</button>
    </form>
    """
    return generate_html_page("User Identification", body, error_message=error)

def get_dob_input_html(name, error=None):
    """HTML for DOB input page."""
    body = f"""
    <p>Hello, {name}!</p>
    <form action="/submit_dob" method="post">
        <label for="dob">Select Your Date of Birth:</label>
        <input type="date" id="dob" name="dob" required>
        <button type="submit">Calculate Age</button>
    </form>
    """
    return generate_html_page("Date of Birth", body, error_message=error)

def get_mode_selection_html(name, age, error=None):
    """HTML for mode selection page."""
    body = f"""
    <p>Name: {name}, Age: {age} years</p>
    <form action="/submit_mode" method="post">
        <label for="mode">Select Smart Assessment Mode:</label>
        <select id="mode" name="mode" required>
            <option value="">-- Select Mode --</option>
            <option value="Default">Default</option>
            <option value="Gym">Gym</option>
            <option value="Sports">Sports</option>
            <option value="Sleep">Sleep</option>
            <option value="Rest">Rest</option>
        </select>
        <button type="submit">Proceed</button>
    </form>
    """
    return generate_html_page("Assessment Mode Selection", body, error_message=error)

def get_param_input_html(page_type, name, mode, error=None):
    """HTML for parameter input pages (0min, 10min, 15min)."""
    title_map = {
        "0min": "0 Minute Parameter Reading",
        "10min": "10 Minute Parameter Reading",
        "15min": "15 Minute Parameter Reading"
    }
    action_map = {
        "0min": "/submit_param_0min",
        "10min": "/submit_param_10min",
        "15min": "/submit_param_15min"
    }
    temp_field = ""
    if page_type in ["0min", "15min"]:
        temp_field = """
        <label for="body_temp">Body Temperature (°F):</label>
        <input type="number" id="body_temp" name="body_temp" step="0.1" required>
        """
    
    body = f"""
    <p>Name: {name}, Mode: {mode}</p>
    <form action="{action_map[page_type]}" method="post">
        <label for="hr">Heart Rate (bpm):</label>
        <input type="number" id="hr" name="hr" required>

        <label for="sbp">Systolic Blood Pressure (mmHg):</label>
        <input type="number" id="sbp" name="sbp" required>

        <label for="dbp">Diastolic Blood Pressure (mmHg):</label>
        <input type="number" id="dbp" name="dbp" required>

        <label for="spo2">SpO2 Level (%):</label>
        <input type="number" id="spo2" name="spo2" step="0.1" required>
        
        {temp_field}

        <button type="submit">Submit</button>
    </form>
    """
    return generate_html_page(title_map[page_type], body, error_message=error)

def get_hr_5min_input_html(name, mode, error=None):
    """HTML for 5 minute HR input."""
    body = f"""
    <p>Name: {name}, Mode: {mode}</p>
    <form action="/submit_hr_5min" method="post">
        <label for="hr">Heart Rate after 5 Minutes (bpm):</label>
        <input type="number" id="hr" name="hr" required>
        <button type="submit">Submit</button>
    </form>
    """
    return generate_html_page("5 Minute Heart Rate Reading", body, error_message=error)

def get_epilepsy_question_html(error=None):
    """HTML for epilepsy question."""
    body = f"""
    <form action="/submit_epilepsy_answer" method="post">
        <label>Do you have medically proved epilepsy? (Yes/No):</label>
        <div style="display: flex; justify-content: center; gap: 20px; margin-bottom: 20px;">
            <input type="radio" id="epilepsy_yes" name="epilepsy_answer" value="Yes" required>
            <label for="epilepsy_yes">Yes</label>
            <input type="radio" id="epilepsy_no" name="epilepsy_answer" value="No">
            <label for="epilepsy_no">No</label>
        </div>
        <button type="submit">Submit</button>
    </form>
    """
    return generate_html_page("Epilepsy Information", body, error_message=error)

def get_asthma_question_html(error=None):
    """HTML for asthma question."""
    body = f"""
    <form action="/submit_asthma_answer" method="post">
        <label>Do you have medically proved asthma? (Yes/No):</label>
        <div style="display: flex; justify-content: center; gap: 20px; margin-bottom: 20px;">
            <input type="radio" id="asthma_yes" name="asthma_answer" value="Yes" required>
            <label for="asthma_yes">Yes</label>
            <input type="radio" id="asthma_no" name="asthma_answer" value="No">
            <label for="asthma_no">No</label>
        </div>
        <button type="submit">Submit</button>
    </form>
    """
    return generate_html_page("Asthma Information", body, error_message=error)

def get_symptom_checker_html(all_symptoms, error=None):
    """HTML for symptom checker."""
    symptom_checkboxes = ""
    for symptom in all_symptoms:
        symptom_checkboxes += f"""
        <label>
            <input type="checkbox" name="symptoms" value="{symptom}">
            {symptom}
        </label>
        """
    body = f"""
    <form action="/submit_symptoms" method="post">
        <label>Select the symptoms you are experiencing:</label>
        <div class="checkbox-group">
            {symptom_checkboxes}
        </div>
        <button type="submit">Check Results</button>
    </form>
    """
    return generate_html_page("Disease Symptom Checker", body, error_message=error)

def get_risk_class(percentage_str):
    """Determines the CSS class for risk color-coding."""
    if isinstance(percentage_str, (int, float)):
        percentage = percentage_str
    else:
        match = re.search(r'(\d+(\.\d+)?) %', percentage_str)
        if match:
            percentage = float(match.group(1))
        else:
            return "risk-neutral" # Default if no percentage found

    if percentage > 60:
        return "risk-high"
    elif 30 <= percentage <= 60:
        return "risk-medium"
    else:
        return "risk-low"

def format_section(title, data_dict):
    """Helper to format data sections with risk color-coding."""
    content = ""
    for key, value in data_dict.items():
        # Replace newlines for HTML display
        formatted_value = value.replace("\n", "<br>")
        
        # Apply risk coloring to percentage values
        # This regex looks for a number followed by " %"
        def replace_with_color(match):
            percentage_value = match.group(0) # e.g., "50 %"
            css_class = get_risk_class(percentage_value)
            return f'<span class="{css_class}">{percentage_value}</span>'

        # Apply coloring to percentages within the string
        formatted_value_with_color = re.sub(r'\d+(\.\d+)? %', replace_with_color, formatted_value)
        
        content += f"<p><strong>{key}:</strong><br>{formatted_value_with_color}</p>"
    return f"""
    <div class="result-section">
        <h3>{title}</h3>
        {content}
    </div>
    """

def get_results_html(results_data):
    """HTML for displaying final results."""
    
    cardiac_status_html = format_section("Cardiac Status", results_data.get("Cardiac Status", {}))
    neurological_status_html = format_section("Neurological Status", results_data.get("Neurological Status", {}))
    weatherly_effect_status_html = format_section("Weatherly Effect Status", results_data.get("Weatherly Effect Status", {}))
    cardiovascular_status_html = format_section("Cardiovascular Status", results_data.get("Cardiovascular Status", {}))
    respiratory_status_html = format_section("Respiratory Status", results_data.get("Respiratory Status", {}))
    mental_status_html = format_section("Mental Status", results_data.get("Mental Status", {}))
    
    body = f"""
    <h2>Assessment Results</h2>
    <div class="button-group">
        <button onclick="showSection('cardiac')">Cardiac Status</button>
        <button onclick="showSection('neurological')">Neurological Status</button>
        <button onclick="showSection('weatherly')">Weatherly Effect Status</button>
        <button onclick="showSection('cardiovascular')">Cardiovascular Status</button>
        <button onclick="showSection('respiratory')">Respiratory Status</button>
        <button onclick="showSection('mental')">Mental Status</button>
    </div>

    <div id="cardiac" class="result-content" style="display:block;">{cardiac_status_html}</div>
    <div id="neurological" class="result-content" style="display:none;">{neurological_status_html}</div>
    <div id="weatherly" class="result-content" style="display:none;">{weatherly_effect_status_html}</div>
    <div id="cardiovascular" class="result-content" style="display:none;">{cardiovascular_status_html}</div>
    <div id="respiratory" class="result-content" style="display:none;">{respiratory_status_html}</div>
    <div id="mental" class="result-content" style="display:none;">{mental_status_html}</div>

    <script>
        function showSection(sectionId) {{
            const sections = document.querySelectorAll('.result-content');
            sections.forEach(section => {{
                section.style.display = 'none';
            }});
            document.getElementById(sectionId).style.display = 'block';
        }}
    </script>
    """
    return generate_html_page("Health Assessment Results", body)


class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(get_homepage_html().encode('utf-8'))
        elif path == '/start_assessment':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(get_name_input_html().encode('utf-8'))
        elif path == '/about':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(get_about_html().encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(generate_html_page("404 Not Found", "<p>The page you requested was not found.</p>").encode('utf-8'))

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = urllib.parse.parse_qs(post_data)

        if path == '/submit_name':
            name = params.get('name', [''])[0].strip()
            if name:
                user_data['name'] = name
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_dob_input_html(name).encode('utf-8'))
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_name_input_html(error="Please enter your name.").encode('utf-8'))

        elif path == '/submit_dob':
            dob_str = params.get('dob', [''])[0]
            if dob_str:
                try:
                    user_age = calculate_age(dob_str)
                    user_data['age'] = user_age

                    # Determine age range
                    if 0 < user_age <= 10:
                        age_range = 1
                    elif 10 < user_age <= 20:
                        age_range = 2
                    elif 20 < user_age <= 30:
                        age_range = 3
                    elif 30 < user_age <= 40:
                        age_range = 4
                    elif 40 < user_age <= 50:
                        age_range = 5
                    elif 50 < user_age <= 60:
                        age_range = 6
                    elif 60 < user_age <= 70:
                        age_range = 7
                    elif 70 < user_age <= 80:
                        age_range = 8
                    elif 80 < user_age <= 90:
                        age_range = 9
                    elif 90 < user_age <= 100:
                        age_range = 10
                    else:
                        age_range = None # Handle out of defined range or error

                    user_data['age_range'] = age_range
                    HR_U, HR_L, SBP_ref, DBP_ref, SpO2_ref = get_parameters_from_df(age_range)
                    user_data['HR_U_ref'] = HR_U
                    user_data['HR_L_ref'] = HR_L
                    user_data['SBP_ref'] = SBP_ref
                    user_data['DBP_ref'] = DBP_ref
                    user_data['SpO2_ref'] = SpO2_ref

                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(get_mode_selection_html(user_data['name'], user_age).encode('utf-8'))
                except ValueError:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(get_dob_input_html(user_data.get('name', 'User'), error="Invalid date format. Please use YYYY-MM-DD.").encode('utf-8'))
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_dob_input_html(user_data.get('name', 'User'), error="Please select your date of birth.").encode('utf-8'))

        elif path == '/submit_mode':
            mode = params.get('mode', [''])[0]
            if mode:
                user_data['mode'] = mode

                # Mode Categorization based on model.py logic
                if mode == "Default":
                    HR_M_L = user_data['HR_L_ref']
                    HR_M_U = user_data['HR_U_ref']
                    SBP_M_L = user_data['SBP_ref'] - 10
                    SBP_M_U = user_data['SBP_ref'] + 10
                    DBP_M_L = user_data['DBP_ref'] - 5
                    DBP_M_U = user_data['DBP_ref'] + 5
                    SpO2_M = user_data['SpO2_ref']
                elif mode == "Rest":
                    HR_M_L = 60
                    HR_M_U = 80
                    SBP_M_L = 105
                    SBP_M_U = 125
                    DBP_M_L = 65
                    DBP_M_U = 85
                    SpO2_M = 95
                elif mode == "Sleep":
                    HR_M_L = 50
                    HR_M_U = 70
                    SBP_M_L = 90
                    SBP_M_U = 110
                    DBP_M_L = 55
                    DBP_M_U = 75
                    SpO2_M = 95
                elif mode == "Gym":
                    HR_M_L = 100
                    HR_M_U = 140
                    SBP_M_L = 120
                    SBP_M_U = 150
                    DBP_M_L = 70
                    DBP_M_U = 100
                    SpO2_M = 90
                elif mode == "Sports":
                    HR_M_L = 100
                    HR_M_U = 150
                    SBP_M_L = 120
                    SBP_M_U = 160
                    DBP_M_L = 75
                    DBP_M_U = 100
                    SpO2_M = 90
                else:
                    # Fallback or error handling for invalid mode
                    HR_M_L, HR_M_U, SBP_M_L, SBP_M_U, DBP_M_L, DBP_M_U, SpO2_M = (None,) * 7
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(get_mode_selection_html(user_data['name'], user_data['age'], error="Error occurred in Mode Selection. Please try again.").encode('utf-8'))
                    return

                user_data['HR_M_L'] = HR_M_L
                user_data['HR_M_U'] = HR_M_U
                user_data['SBP_M_L'] = SBP_M_L
                user_data['SBP_M_U'] = SBP_M_U
                user_data['DBP_M_L'] = DBP_M_L
                user_data['DBP_M_U'] = DBP_M_U
                user_data['SpO2_M'] = SpO2_M

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_param_input_html("0min", user_data['name'], mode).encode('utf-8'))
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_mode_selection_html(user_data['name'], user_data['age'], error="Please select your assessment mode.").encode('utf-8'))

        elif path == '/submit_param_0min':
            try:
                HR_1 = int(params.get('hr', [''])[0])
                SBP_1 = int(params.get('sbp', [''])[0])
                DBP_1 = int(params.get('dbp', [''])[0])
                SpO2_1 = float(params.get('spo2', [''])[0])
                body_temp_1 = float(params.get('body_temp', [''])[0])

                user_data['HR_1'] = HR_1
                user_data['SBP_1'] = SBP_1
                user_data['DBP_1'] = DBP_1
                user_data['SpO2_1'] = SpO2_1
                user_data['body_temp_1'] = body_temp_1

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_hr_5min_input_html(user_data['name'], user_data['mode']).encode('utf-8'))
            except ValueError:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_param_input_html("0min", user_data['name'], user_data['mode'], error="Please enter valid numbers for all parameters.").encode('utf-8'))

        elif path == '/submit_hr_5min':
            try:
                HR_2 = int(params.get('hr', [''])[0])
                user_data['HR_2'] = HR_2

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_param_input_html("10min", user_data['name'], user_data['mode']).encode('utf-8'))
            except ValueError:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_hr_5min_input_html(user_data['name'], user_data['mode'], error="Please enter a valid number for Heart Rate.").encode('utf-8'))

        elif path == '/submit_param_10min':
            try:
                HR_3 = int(params.get('hr', [''])[0])
                SBP_2 = int(params.get('sbp', [''])[0])
                DBP_2 = int(params.get('dbp', [''])[0])
                SpO2_2 = float(params.get('spo2', [''])[0])

                user_data['HR_3'] = HR_3
                user_data['SBP_2'] = SBP_2
                user_data['DBP_2'] = DBP_2
                user_data['SpO2_2'] = SpO2_2

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_param_input_html("15min", user_data['name'], user_data['mode']).encode('utf-8'))
            except ValueError:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_param_input_html("10min", user_data['name'], user_data['mode'], error="Please enter valid numbers for all parameters.").encode('utf-8'))

        elif path == '/submit_param_15min':
            try:
                HR_4 = int(params.get('hr', [''])[0])
                SBP_3 = int(params.get('sbp', [''])[0])
                DBP_3 = int(params.get('dbp', [''])[0])
                SpO2_3 = float(params.get('spo2', [''])[0])
                body_temp_2 = float(params.get('body_temp', [''])[0])

                user_data['HR_4'] = HR_4
                user_data['SBP_3'] = SBP_3
                user_data['DBP_3'] = DBP_3
                user_data['SpO2_3'] = SpO2_3
                user_data['body_temp_2'] = body_temp_2

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_epilepsy_question_html().encode('utf-8'))
            except ValueError:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_param_input_html("15min", user_data['name'], user_data['mode'], error="Please enter valid numbers for all parameters.").encode('utf-8'))

        elif path == '/submit_epilepsy_answer':
            epilepsy_answer = params.get('epilepsy_answer', [''])[0]
            if epilepsy_answer in ["Yes", "No"]:
                user_data['epilepsy_answer'] = epilepsy_answer
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_asthma_question_html().encode('utf-8'))
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_epilepsy_question_html(error="Please select Yes or No.").encode('utf-8'))

        elif path == '/submit_asthma_answer':
            asthma_answer = params.get('asthma_answer', [''])[0]
            if asthma_answer in ["Yes", "No"]:
                user_data['asthma_answer'] = asthma_answer
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_symptom_checker_html(all_symptoms).encode('utf-8'))
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(get_asthma_question_html(error="Please select Yes or No.").encode('utf-8'))

        elif path == '/submit_symptoms':
            selected_symptoms = params.get('symptoms', [])
            user_data['selected_symptoms'] = selected_symptoms

            # --- Start of Calculation Logic (from model.py) ---
            HR_1 = user_data['HR_1']
            HR_2 = user_data['HR_2']
            HR_3 = user_data['HR_3']
            HR_4 = user_data['HR_4']
            SBP_1 = user_data['SBP_1']
            SBP_2 = user_data['SBP_2']
            SBP_3 = user_data['SBP_3']
            DBP_1 = user_data['DBP_1']
            DBP_2 = user_data['DBP_2']
            DBP_3 = user_data['DBP_3']
            SpO2_1 = user_data['SpO2_1']
            SpO2_2 = user_data['SpO2_2']
            SpO2_3 = user_data['SpO2_3']
            body_temp_1 = user_data['body_temp_1']
            body_temp_2 = user_data['body_temp_2']
            mode = user_data['mode']
            HR_M_L = user_data['HR_M_L']
            HR_M_U = user_data['HR_M_U']
            SBP_M_L = user_data['SBP_M_L']
            SBP_M_U = user_data['SBP_M_U']
            DBP_M_L = user_data['DBP_M_L']
            DBP_M_U = user_data['DBP_M_U']
            SpO2_M = user_data['SpO2_M']
            epilepsy_answer = user_data['epilepsy_answer']
            asthma_answer = user_data['asthma_answer']

            # Screen the parameters.
            # Heart Rate Screened.
            HR_D10 = abs(HR_1 - HR_3)
            HR_D15 = abs(HR_1 - HR_4)

            HR_21 = HR_2 - HR_1
            HR_32 = HR_3 - HR_2
            HR_43 = HR_4 - HR_3

            if HR_21 >= 3 and HR_32 >= 3 and HR_43 >= 3:
                command_HR = "aff"
            elif HR_21 <= -3 and HR_32 <= -3 and HR_43 <= -3:
                command_HR = "neg"
            elif -3 < HR_21 < 3 and -3 < HR_32 < 3 and -3 < HR_43 < 3:
                command_HR = "nor"
            else:
                command_HR = "irr"

            HR_N = HR_1
            HR_F = HR_4
            HR_avg = (HR_1 + HR_2 + HR_3 + HR_4)/4

            HR_scale = 20

            HR_risk_10 = abs(HR_1 - HR_3) * 100/HR_scale
            HR_risk_15 = abs(HR_4 - HR_1) * 100/HR_scale

            HR_U_S = user_data['HR_U_ref'] - 15 # This was HR_U - 15 in original, using ref value

            # Screen BP.
            SBP_10 = abs(SBP_1 - SBP_2)
            SBP_15 = abs(SBP_1 - SBP_3)
            DBP_10 = abs(DBP_1 - DBP_2)
            DBP_15 = abs(DBP_1 - DBP_3)

            SBP_avg = (SBP_1 + SBP_2 + SBP_3)/3
            DBP_avg = (DBP_1 + DBP_2 + DBP_3)/3

            SBP_N = SBP_1
            DBP_N = DBP_1
            SBP_F = SBP_3
            DBP_F = DBP_3

            SBP_scale = 20
            DBP_scale = 10

            SBP_risk_10 = abs(SBP_1 - SBP_2) * 100/SBP_scale
            DBP_risk_10 = abs(DBP_1 - DBP_2) * 100/DBP_scale
            SBP_risk_15 = abs(SBP_1 - SBP_3) * 100/SBP_scale
            DBP_risk_15 = abs(DBP_1 - DBP_3) * 100/DBP_scale

            # Screened SpO2.
            SpO2_10 = SpO2_1 - SpO2_2
            SpO2_15 = SpO2_1 - SpO2_3

            if mode == "Default":
                SpO2_G = 1.5
            elif mode == "Rest":
                SpO2_G = 1
            elif mode == "Sleep":
                SpO2_G = 0.5
            elif mode == "Gym":
                SpO2_G = 2
            elif mode == "Sports":
                SpO2_G = 2.5
            else:
                SpO2_G = 1.0 # Default if mode is somehow invalid

            command_O = "Nor" # Initialize
            if SpO2_G >= SpO2_10 >= 0:
                command_O_10 = "Nor"
            elif SpO2_G < SpO2_10:
                command_O_10 = "High"
            elif SpO2_10 < 0:
                command_O_10 = "Rev"

            if SpO2_G >= SpO2_15 >= 0:
                command_O_15 = "Nor"
            elif SpO2_G < SpO2_15:
                command_O_15 = "High"
            elif SpO2_15 < 0:
                command_O_15 = "Rev"

            SpO2_risk_10 = abs(SpO2_10) * 100/SpO2_G
            SpO2_risk_15 = abs(SpO2_15) * 100/SpO2_G

            # Screened Body Temperature.
            body_temp_C = abs(body_temp_1 - body_temp_2)

            if 100.5 >= body_temp_2 >= 99.5:
                command_temp = 1
            elif body_temp_2 > 100.5:
                command_temp = 2
            elif 97.5 >= body_temp_2 >= 95:
                command_temp = 3
            elif 95 > body_temp_2:
                command_temp = 4
            else:
                command_temp = 5 # Normal or undefined range

            # Search for Cardiac Conditions.
            # Cardiac Abnormalities.
            if command_HR == "aff":
                heart = "tachycardia"
            elif command_HR == "neg":
                heart = "bradycardia"
            elif command_HR == "irr":
                heart = "arrhythmia"
            else:
                heart = "normal"

            HR_risk = 0 # Initialize
            if heart == "tachycardia":
                HR_rate = (HR_21 + HR_32 + HR_43)/3
                HR_risk = HR_risk_15
                HR_text = f"You are at a tachycardial tendency with {HR_risk:.2f} % risk<br>Your average heart rate increase is {HR_rate:.2f} bpm"
                HR_ref = "T"
            elif heart == "bradycardia":
                HR_rate = abs((HR_21 + HR_32 + HR_43)/3)
                HR_risk = HR_risk_15
                HR_text = f"You are at a bradycardial tendency with {HR_risk:.2f} % risk<br>Your average heart rate decrease is {HR_rate:.2f} bpm"
                HR_ref = "B"
            elif heart == "arrhythmia":
                HR_rate = (abs(HR_21) + abs(HR_32) + abs(HR_43))/3
                HR_risk = HR_rate * 3 * 100/30 # Assuming 30 is a max fluctuation for 100% risk
                HR_text = f"You are at a arrhythmial tendency with {HR_risk:.2f} % risk<br>Your average heart rate fluctuation is {HR_rate:.2f} bpm"
                HR_ref = "A"
            else:
                HR_text = "No cardiac abnormality noticed"
                HR_ref = "N"

            # Determine cardiac state.
            HR_state_C = "Normal"
            if mode == "Default" and HR_ref == "T" and HR_4 > HR_M_U:
                HR_state_C = "Tachycardial"
            elif mode == "Default" and HR_ref == "B" and HR_4 < HR_M_L:
                HR_state_C = "Bradycardial"
            elif mode == "Sleep" and HR_ref == "T" and HR_4 > HR_M_U:
                HR_state_C = "Tachycardial"
            elif mode == "Sleep" and HR_ref == "B" and HR_4 < HR_M_L:
                HR_state_C = "Bradycardial"
            elif mode == "Sports" and HR_ref == "T" and HR_4 > HR_M_U:
                HR_state_C = "Tachycardial"
            elif mode == "Sports" and HR_ref == "B" and HR_4 < HR_M_L:
                HR_state_C = "Bradycardial"
            elif mode == "Gym" and HR_ref == "T" and HR_4 > HR_M_U:
                HR_state_C = "Tachycardial"
            elif mode == "Gym" and HR_ref == "B" and HR_4 < HR_M_L:
                HR_state_C = "Bradycardial"
            elif mode == "Rest" and HR_ref == "T" and HR_4 > HR_M_U:
                HR_state_C = "Tachycardial"
            elif mode == "Rest" and HR_ref == "B" and HR_4 < HR_M_L:
                HR_state_C = "Bradycardial"
            elif HR_ref == "A":
                HR_state_C = "Arrhythmial"

            HR_state_P = "Normal"
            if mode == "Default" and HR_1 > HR_M_U:
                HR_state_P = "Tachycardial"
            elif mode == "Default" and HR_1 < HR_M_L:
                HR_state_P = "Bradycardial"
            elif mode == "Sleep" and HR_1 > HR_M_U:
                HR_state_P = "Tachycardial"
            elif mode == "Sleep" and HR_1 < HR_M_L:
                HR_state_P = "Bradycardial"
            elif mode == "Sports" and HR_1 > HR_M_U:
                HR_state_P = "Tachycardial"
            elif mode == "Sports" and HR_1 < HR_M_L:
                HR_state_P = "Bradycardial"
            elif mode == "Gym" and HR_1 > HR_M_U:
                HR_state_P = "Tachycardial"
            elif mode == "Gym" and HR_1 < HR_M_L:
                HR_state_P = "Bradycardial"
            elif mode == "Rest" and HR_1 > HR_M_U:
                HR_state_P = "Tachycardial"
            elif mode == "Rest" and HR_1 < HR_M_L:
                HR_state_P = "Bradycardial"
            elif HR_ref == "A" and HR_1 > HR_M_U:
                HR_state_P = "Tachycardial"
            elif HR_ref == "A" and HR_1 < HR_M_L:
                HR_state_P = "Bradycardial"
            elif HR_ref == "A" and HR_M_U >= HR_1 >= HR_M_L:
                HR_state_P = "Normal"

            # Heart Attack.
            HA_text = "Negative"
            HA_risk = 0
            if (HR_ref == "T" and SBP_1 < SBP_2 < SBP_3 and DBP_1 < DBP_2 < DBP_3 and SpO2_1 > SpO2_2 > SpO2_3) or \
               (HR_ref == "B" and SBP_1 > SBP_2 > SBP_3 and DBP_1 > DBP_2 > DBP_3 and SpO2_1 > SpO2_2 > SpO2_3) or \
               (HR_ref == "A" and SBP_1 > SBP_2 > SBP_3 and DBP_1 > DBP_2 > DBP_3 and SpO2_1 > SpO2_2 > SpO2_3):
                HA_risk = ((((SBP_risk_15 + DBP_risk_15)/2) + HR_risk)/2) * SpO2_risk_15/100
                HA_text = f"{HA_risk:.2f} %"

            # Heart Failure.
            HF_text = "Negative"
            HF_risk = 0
            if HR_state_P == "Tachycardial":
                HF_risk = ((((SBP_risk_15 + DBP_risk_15)/2) + HR_risk)/2) * SpO2_risk_15/100
                HF_text = f"{HF_risk:.2f} %"

            # Search for Neurological Conditions.
            # Brain Stroke.
            BS_text = "Negative"
            BS_risk = 0
            if HR_1 < HR_2 < HR_3 < HR_4 and SBP_1 < SBP_2 < SBP_3 and DBP_1 < DBP_2 < DBP_3 and SpO2_1 > SpO2_2 > SpO2_3:
                BS_risk = ((DBP_risk_15 + SBP_risk_15 + HR_risk_15)/3) * SpO2_risk_15/100
                BS_text = f"{BS_risk:.2f} %"

            # Epilepsy.
            E_risk = 0
            E_info = "No"
            if HR_1 < HR_2 < HR_3 < HR_4 and SBP_1 < SBP_2 < SBP_3 and DBP_1 < DBP_2 < DBP_3 and SpO2_1 > SpO2_2 > SpO2_3:
                E_risk = ((DBP_risk_15 + SBP_risk_15 + HR_risk_15)/3) * SpO2_risk_15/100
                E_info = "Yes"

            E_text = "Negative"
            if E_info == "No":
                E_text = "Negative"
            elif E_info == "Yes" and epilepsy_answer == "Yes":
                E_text = f"{E_risk:.2f} %"
            elif E_info == "Yes" and epilepsy_answer == "No":
                E_text = "Negative"

            # Sleep Paralysis.
            SP_text = "Negative"
            SP_risk = 0
            if HR_1 < HR_2 < HR_3 and SBP_1 < SBP_2 and DBP_1 < DBP_2 and mode == "Sleep":
                SP_risk = (((SBP_risk_10 + DBP_risk_10)/2) + HR_risk_10)/2
                SP_text = f"{SP_risk:.2f} %"

            # Search for Cardiovascular Conditions.
            # Decide Stage.
            BP_state_P = "Normal"
            if mode == "Default" and SBP_1 > SBP_M_U and DBP_1 > DBP_M_U:
                BP_state_P = "Hypertensive"
            elif mode == "Default" and SBP_1 < SBP_M_L and DBP_1 < DBP_M_L:
                BP_state_P = "Hypotensive"
            elif mode == "Sleep" and SBP_1 > SBP_M_U and DBP_1 > DBP_M_U:
                BP_state_P = "Hypertensive"
            elif mode == "Sleep" and SBP_1 < SBP_M_L and DBP_1 < DBP_M_L:
                BP_state_P = "Hypotensive"
            elif mode == "Rest" and SBP_1 > SBP_M_U and DBP_1 > DBP_M_U:
                BP_state_P = "Hypertensive"
            elif mode == "Rest" and SBP_1 < SBP_M_L and DBP_1 < DBP_M_L:
                BP_state_P = "Hypotensive"
            elif mode == "Gym" and SBP_1 > SBP_M_U and DBP_1 > DBP_M_U:
                BP_state_P = "Hypertensive"
            elif mode == "Gym" and SBP_1 < SBP_M_L and DBP_1 < DBP_M_L:
                BP_state_P = "Hypotensive"
            elif mode == "Sports" and SBP_1 > SBP_M_U and DBP_1 > DBP_M_U:
                BP_state_P = "Hypertensive"
            elif mode == "Sports" and SBP_1 < SBP_M_L and DBP_1 < DBP_M_L:
                BP_state_P = "Hypotensive"

            BP_state_C = "Normal"
            if mode == "Default" and SBP_3 > SBP_M_U and DBP_3 > DBP_M_U: # Using SBP_3, DBP_3 for current state
                BP_state_C = "Hypertensive"
            elif mode == "Default" and SBP_3 < SBP_M_L and DBP_3 < DBP_M_L:
                BP_state_C = "Hypotensive"
            elif mode == "Sleep" and SBP_3 > SBP_M_U and DBP_3 > DBP_M_U:
                BP_state_C = "Hypertensive"
            elif mode == "Sleep" and SBP_3 < SBP_M_L and DBP_3 < DBP_M_L:
                BP_state_C = "Hypotensive"
            elif mode == "Rest" and SBP_3 > SBP_M_U and DBP_3 > DBP_M_U:
                BP_state_C = "Hypertensive"
            elif mode == "Rest" and SBP_3 < SBP_M_L and DBP_3 < DBP_M_L:
                BP_state_C = "Hypotensive"
            elif mode == "Gym" and SBP_3 > SBP_M_U and DBP_3 > DBP_M_U:
                BP_state_C = "Hypertensive"
            elif mode == "Gym" and SBP_3 < SBP_M_L and DBP_3 < DBP_M_L:
                BP_state_C = "Hypotensive"
            elif mode == "Sports" and SBP_3 > SBP_M_U and DBP_3 > DBP_M_U:
                BP_state_C = "Hypertensive"
            elif mode == "Sports" and SBP_3 < SBP_M_L and DBP_3 < DBP_M_L:
                BP_state_C = "Hypotensive"

            BP_text = "Normal"
            if BP_state_C == "Hypertensive" and BP_state_P == "Hypertensive":
                BP_text = "Constant Hypertensive Tendency"
            elif BP_state_C == "Hypotensive" and BP_state_P == "Hypotensive":
                BP_text = "Constant Hypotensive Tendency"
            elif BP_state_C == "Hypertensive" and BP_state_P == "Hypotensive":
                BP_text = "Chronic Hypertensive Tendency"
            elif BP_state_C == "Hypotensive" and BP_state_P == "Hypertensive":
                BP_text = "Chronic Hypotensive Tendency"
            elif BP_state_C == "Hypertensive" and BP_state_P == "Normal":
                BP_text = "Acute Hypertensive Tendency"
            elif BP_state_C == "Hypotensive" and BP_state_P == "Normal":
                BP_text = "Acute Hypotensive Tendency"

            # Search for Respiratory Disorders.
            # Asthma.
            A_info = "No"
            A_risk = 0
            if HR_1 < HR_2 < HR_3 and SBP_1 < SBP_2 and DBP_1 < DBP_2 and SpO2_1 > SpO2_2:
                A_risk = (((HR_risk_10 + SBP_risk_10 + DBP_risk_10)/3) * SpO2_risk_10/100)
                A_info = "Yes"

            A_text = "Negative"
            if A_info == "Yes" and asthma_answer == "Yes":
                A_text = f"{A_risk:.2f} %"

            # Pulmonary Embolism.
            PE_text = "Negative"
            PE_risk = 0
            if HR_1 < HR_2 < HR_3 < HR_4 and SBP_1 < SBP_2 < SBP_3 and DBP_1 < DBP_2 < DBP_3 and SpO2_1 > SpO2_2 > SpO2_3:
                PE_risk = ((((SBP_risk_15 + DBP_risk_15)/2) + HR_risk_15)/2) * SpO2_risk_15/100
                PE_text = f"{PE_risk:.2f} %"

            # Search for Temperature Related Conditions.
            # Heat Stroke and Hypothermia.
            T_type_1 = "Heat Exhaustion"
            T_type_2 = "Heat Stroke"
            T_text_1 = "0 %"
            T_text_2 = "0 %"
            T_type_text = "None"

            if command_temp == 1 and HR_1 < HR_2 < HR_3 < HR_4 and SBP_1 < SBP_2 < SBP_3 and DBP_1 < DBP_2 < DBP_3 and SpO2_1 > SpO2_2 > SpO2_3:
                body_temp_risk_1 = (body_temp_2 - body_temp_1) * 100/(100.5 - body_temp_1) if (100.5 - body_temp_1) != 0 else 0
                body_temp_risk_2 = (body_temp_2 - body_temp_1) * 100/(104.0 - body_temp_1) if (104.0 - body_temp_1) != 0 else 0
                T_risk_1 = ((SBP_risk_15 + DBP_risk_15 + HR_risk_15 + SpO2_risk_15)/4) * body_temp_risk_1/100
                T_risk_2 = ((SBP_risk_15 + DBP_risk_15 + HR_risk_15 + SpO2_risk_15)/4) * body_temp_risk_2/100
                T_text_1 = f"{T_risk_1:.2f} %"
                T_text_2 = f"{T_risk_2:.2f} %"
                T_type_text = f"{T_type_1} and {T_type_2}"
            elif command_temp == 2 and HR_1 < HR_2 < HR_3 < HR_4 and SBP_1 < SBP_2 < SBP_3 and DBP_1 < DBP_2 < DBP_3 and SpO2_1 > SpO2_2 > SpO2_3:
                body_temp_risk = (body_temp_2 - body_temp_1) * 100/(104.0 - body_temp_1) if (104.0 - body_temp_1) != 0 else 0
                T_risk_1 = 100
                T_risk_2 = ((SBP_risk_15 + DBP_risk_15 + HR_risk_15 + SpO2_risk_15)/4) * body_temp_risk/100
                T_text_1 = f"{T_risk_1:.2f} %"
                T_text_2 = f"{T_risk_2:.2f} %"
                T_type_text = f"{T_type_1} and {T_type_2}"
            elif command_temp == 3 and HR_1 > HR_2 > HR_3 > HR_4 and SBP_1 > SBP_2 > SBP_3 and DBP_1 > DBP_2 > DBP_3 and SpO2_1 > SpO2_2 > SpO2_3:
                T_type_1 = "Cold Exhaustion"
                T_type_2 = "Hypothermia"
                body_temp_risk_1 = (body_temp_1 - body_temp_2) * 100/(body_temp_1 - 95.0) if (body_temp_1 - 95.0) != 0 else 0
                body_temp_risk_2 = (body_temp_1 - body_temp_2) * 100/(body_temp_1 - 90.0) if (body_temp_1 - 90.0) != 0 else 0
                T_risk_1 = ((SBP_risk_15 + DBP_risk_15 + HR_risk_15 + SpO2_risk_15)/4) * body_temp_risk_1/100
                T_risk_2 = ((SBP_risk_15 + DBP_risk_15 + HR_risk_15 + SpO2_risk_15)/4) * body_temp_risk_2/100
                T_text_1 = f"{T_risk_1:.2f} %"
                T_text_2 = f"{T_risk_2:.2f} %"
                T_type_text = f"{T_type_1} and {T_type_2}"
            elif command_temp == 4 and HR_1 > HR_2 > HR_3 > HR_4 and SBP_1 > SBP_2 > SBP_3 and DBP_1 > DBP_2 > DBP_3 and SpO2_1 > SpO2_2 > SpO2_3:
                T_type_1 = "Cold Exhaustion"
                T_type_2 = "Hypothermia"
                body_temp_risk = (body_temp_1 - body_temp_2) * 100/(body_temp_1 - 90.0) if (body_temp_1 - 90.0) != 0 else 0
                T_risk_1 = 100
                T_risk_2 = ((SBP_risk_15 + DBP_risk_15 + HR_risk_15 + SpO2_risk_15)/4) * body_temp_risk/100
                T_text_1 = f"{T_risk_1:.2f} %"
                T_text_2 = f"{T_risk_2:.2f} %"
                T_type_text = f"{T_type_1} and {T_type_2}"

            # Search for Mental Disorders.
            # Anxiety.
            An_text = "Negative"
            An_risk = 0
            if HR_1 < HR_2 < HR_3 and SBP_1 < SBP_2 and DBP_1 < DBP_2 and SpO2_1 < SpO2_2:
                An_risk = ((((DBP_risk_10 + SBP_risk_10)/2) + HR_risk_10)/2) * SpO2_risk_10/100
                An_text = f"{An_risk:.2f} %"

            # Stress.
            S_type = "No"
            S_text = "Negative"
            S_risk = 0
            if HR_1 < HR_2 < HR_3 < HR_4 and SBP_1 < SBP_2 < SBP_3 and DBP_1 < DBP_2 < DBP_3 and SpO2_1 < SpO2_2 < SpO2_3:
                S_type = "Acute"
                S_risk = ((((SBP_risk_15 + DBP_risk_15)/2) + HR_risk_15)/2) * SpO2_risk_15/100
                S_text = f"{S_risk:.2f} %"
            elif mode in ["Default", "Rest", "Sleep"] and HR_avg > HR_M_U and SBP_avg > SBP_M_U and DBP_avg > DBP_M_U:
                S_type = "Chronic"
                S_text = "Positive"

            # Panic Attack.
            PA_text = "Negative"
            PA_risk = 0
            if HR_1 < HR_2 < HR_3 and SBP_1 < SBP_2 and DBP_1 < DBP_2 and SpO2_1 > SpO2_2:
                PA_risk = ((HR_risk_10 + SBP_risk_10 + DBP_risk_10)/2) * SpO2_risk_10/100
                PA_text = f"{PA_risk:.2f} %"

            # Depression.
            D_type = "None"
            if mode in ["Default", "Rest", "Sleep"] and HR_avg > HR_M_U and SBP_avg > SBP_M_U and DBP_avg > DBP_M_U:
                D_type = "Major Depressive Disorder"
            elif mode in ["Default", "Rest", "Sleep"] and SBP_avg > SBP_M_U and DBP_avg > DBP_M_U:
                D_type = "Persistant Depressive Disorder"
            elif mode in ["Default", "Rest", "Sleep"] and HR_avg > HR_M_U:
                D_type = "Seasonal Affective Disorder"

            # Symptom-based assessment (re-calculate based on selected_symptoms)
            symptom_results = {}
            inputted_symptoms_set = set(selected_symptoms)

            for disease, symptoms_list in diseases.items():
                match_count = sum(1 for symptom in inputted_symptoms_set if symptom in symptoms_list)
                percentage = int((match_count / len(symptoms_list)) * 100) if len(symptoms_list) > 0 else 0
                symptom_results[disease] = percentage

            # Map symptom percentages to the output variables
            HA_matched = f"{symptom_results.get('Heart Attack', 0)} %"
            HF_matched = f"{symptom_results.get('Heart Failure', 0)} %"
            BS_matched = f"{symptom_results.get('Brain Stroke', 0)} %"
            HS_matched = f"{symptom_results.get('Heat Stroke', 0)} %"
            H_matched = f"{symptom_results.get('Hypothermia', 0)} %"
            A_matched = f"{symptom_results.get('Asthma', 0)} %"
            PE_matched = f"{symptom_results.get('Pulmonary Embolism', 0)} %"
            E_matched = f"{symptom_results.get('Epilepsy', 0)} %"
            Hyper_matched = f"{symptom_results.get('Hypertensive Disorder', 0)} %"
            Hypo_matched = f"{symptom_results.get('Hypotensive Disorder', 0)} %"
            EHR_matched = f"{symptom_results.get('Tachycardia', 0)} %"
            LHR_matched = f"{symptom_results.get('Bradycardia', 0)} %"
            IHR_matched = f"{symptom_results.get('Arrhythmia', 0)} %"
            An_matched = f"{symptom_results.get('Anxiety', 0)} %"
            S_matched = f"{symptom_results.get('Stress', 0)} %"
            PA_matched = f"{symptom_results.get('Panic Attack', 0)} %"
            SP_matched = f"{symptom_results.get('Sleep Paralysis', 0)} %"
            D_matched = f"{symptom_results.get('Depression', 0)} %"

            # Prepare data for results page
            data_1 = {
                "Primary State": f"Primary State: {HR_state_P}",
                "Current State": f"Current State: {HR_state_C}",
                "Current Tendency": f"Tendency: {heart}",
                "State Symptom Status": f"Symptoms Matched -<br> Tachycardia: {EHR_matched}<br> Bradycardia: {LHR_matched}<br> Arrhythmia: {IHR_matched}",
                "Heart Attack": f"Physical Assessment: {HA_text}<br> Symptom Assessment: {HA_matched}",
                "Heart Failure": f"Physical Assessment: {HF_text}<br> Symptom Assessment: {HF_matched}"
            }

            data_2 = {
                "Brain Stroke": f"Physical Assessment: {BS_text}<br> Symptom Assessment: {BS_matched}",
                "Epilepsy": f"Physical Assessment: {E_text}<br> Symptom Assessment: {E_matched}",
                "Sleep Paralysis": f"Physical Assessment: {SP_text}<br> Symptom Assessment: {SP_matched}"
            }

            data_3 = {
                "Current Possibility": T_type_text,
                "Physical Assessment Status": f"{T_type_1}: {T_text_1}<br> {T_type_2}: {T_text_2}",
                "Symptom Assessment Status": f"Heat Stroke: {HS_matched}<br> Hypothermia: {H_matched}"
            }

            data_4 = {
                "Primary State": f"Primary State: {BP_state_P}",
                "Current State": f"Current State: {BP_state_C}",
                "Current Tendency": f"Current Tendency: {BP_text}",
                "Symptom Assessment Status": f"Hypertension: {Hyper_matched}<br> Hypotension: {Hypo_matched}"
            }

            data_5 = {
                "Asthma": f"Physical Assessment: {A_text}<br> Symptom Assessment: {A_matched}",
                "Pulmonary Embolism": f"Physical Assessment: {PE_text}<br> Symptom Assessment: {PE_matched}"
            }

            data_6 = {
                "Panic Attack": f"Physical Assessment: {PA_text}<br> Symptom Assessment: {PA_matched}",
                "Anxiety": f"Physical Assessment: {An_text}<br> Symptom Assessment: {An_matched}",
                "Stress": f"Stress Type: {S_type}<br> Physical Assessment: {S_text}<br> Symptom Assessment: {S_matched}",
                "Depression": f"Depression Type: {D_type}<br> Symptom Assessment: {D_matched}"
            }

            results_to_display = {
                "Cardiac Status": data_1,
                "Neurological Status": data_2,
                "Weatherly Effect Status": data_3,
                "Cardiovascular Status": data_4,
                "Respiratory Status": data_5,
                "Mental Status": data_6
            }

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(get_results_html(results_to_display).encode('utf-8'))

        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(generate_html_page("404 Not Found", "<p>The page you requested was not found.</p>").encode('utf-8'))

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Serving at port {PORT}")
        print(f"Open your browser and navigate to http://localhost:{PORT}")
        httpd.serve_forever()
