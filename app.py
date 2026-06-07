import streamlit as st
import csv
import random
import azure.cognitiveservices.speech as speechsdk

# --- 1. Page Configuration ---
st.set_page_config(page_title="Virtual Classroom Simulator", layout="wide")
st.title("Virtual Student Simulator")
st.write("Interact with distinct student personas powered by Azure Neural Voices.")

# --- 2. Retrieve Credentials ---
AZURE_KEY = st.secrets["azure_speech"]["key"]
AZURE_REGION = st.secrets["azure_speech"]["region"]

# --- 3. Load the Student Roster from CSVs ---
@st.cache_data
def load_roster():
    female_voices = ["en-GB-MaisieNeural", "en-GB-SoniaNeural", "en-US-JennyNeural", "en-US-JaneNeural", "en-AU-NatashaNeural", "en-CA-ClaraNeural", "en-IN-NeerjaNeural"]
    male_voices = ["en-GB-RyanNeural", "en-GB-ThomasNeural", "en-US-DavisNeural", "en-US-GuyNeural", "en-AU-WilliamNeural", "en-CA-LiamNeural", "en-IN-PrabhatNeural"]
    
    students = []
    
    # Load all three files with their respective age-pitch brackets
    datasets = [
        {"file": "Virtual_Students - Year 7.csv", "year": "Year 7", "pitch_min": 0, "pitch_max": 15},
        {"file": "Virtual_Students - year9.csv", "year": "Year 9", "pitch_min": -10, "pitch_max": 5},
    ]
    
    for dataset in datasets:
        try:
            with open(dataset["file"], mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    if not row.get("Student ID", "").strip():
                        continue
                        
                    # Seed the randomizer so voices remain consistent
                    random.seed(row["Student ID"])
                    
                    gender = row.get("Gender", "").strip().upper()
                    if gender == "M":
                        voice = random.choice(male_voices)
                    elif gender == "F":
                        voice = random.choice(female_voices)
                    else:
                        voice = random.choice(female_voices + male_voices)
                        
                    # Apply the age-specific pitch rules defined in the dataset dictionary
                    pitch_val = random.randint(dataset["pitch_min"], dataset["pitch_max"])
                    rate_val = random.randint(-10, 10)
                    
                    students.append({
                        "id": row["Student ID"],
                        # Add the Year Group to the display name for the sidebar
                        "name": f"{row['Full Name']} ({dataset['year']})", 
                        "voice": voice,
                        "year_group": dataset["year"], # Added for the UI filter
                        "default_style": "cheerful",
                        "pitch_adjust": f"+{pitch_val}%" if pitch_val > 0 else f"{pitch_val}%",
                        "rate_adjust": f"+{rate_val}%" if rate_val > 0 else f"{rate_val}%",
                        "misconception": f"[{dataset['year']}] {row.get('Transition Portrait', '')} MATHS: {row.get('Maths', '')}"
                    })
        except FileNotFoundError:
            st.warning(f"Could not find {dataset['file']}. Please ensure it is uploaded to GitHub.")
            
    return students

# Initialize data and dictionary mapping
students_data = load_roster()
roster_dict = {student["name"]: student for student in students_data}

# --- 4. Sidebar: Student Selection & Profile ---
st.sidebar.header("Classroom Roster")

# UI Filter to quickly swap between cohorts
year_filter = st.sidebar.radio(
    "Filter by Year Group",
    ["All", "Year 7", "Year 9", "Year 10"],
    horizontal=True
)

# Apply the filter to the dictionary
if year_filter == "All":
    filtered_roster = roster_dict
else:
    filtered_roster = {name: data for name, data in roster_dict.items() if data["year_group"] == year_filter}

# Safety catch in case a CSV failed to load
if not filtered_roster:
    st.sidebar.error(f"No students found for {year_filter}. Check that the CSV file is uploaded to GitHub.")
    st.stop()

selected_name = st.sidebar.selectbox("Select a Student", list(filtered_roster.keys()))

active_student = filtered_roster[selected_name]

st.sidebar.subheader("Pedagogical Profile")
st.sidebar.info(active_student.get("misconception", "No notes provided."))
st.sidebar.caption(f"Voice: {active_student['voice']} | Pitch: {active_student['pitch_adjust']} | Rate: {active_student['rate_adjust']}")

current_emotion = st.sidebar.selectbox(
    "Current Emotional State",
    ["cheerful", "sad", "fearful", "angry", "whispering", "excited"],
    index=0
)
intensity = st.sidebar.slider("Emotion Intensity", min_value=0.5, max_value=2.0, value=1.0, step=0.1)

# --- 5. Main Interaction Area ---
text_input = st.text_area(
    f"What is {active_student['name'].split()[0]} saying?",
    value="I think I understand the first part, but I'm completely lost on what to do next."
)

# --- 6. Generate the Audio ---
if st.button(f"Generate Voice"):
    with st.spinner(f"Generating audio for {active_student['name']}..."):
        
        speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
        pull_stream = speechsdk.audio.PullAudioOutputStream()
        stream_config = speechsdk.audio.AudioOutputConfig(stream=pull_stream)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=stream_config)
        
        ssml_payload = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='en-US'>
            <voice name='{active_student['voice']}'>
                <mstts:express-as style='{current_emotion}' styledegree='{intensity}'>
                    <prosody pitch='{active_student['pitch_adjust']}' rate='{active_student['rate_adjust']}'>
                        {text_input}
                    </prosody>
                </mstts:express-as>
            </voice>
        </speak>
        """
        
        result = synthesizer.speak_ssml_async(ssml_payload).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_data = result.audio_data
            st.success("Audio generated successfully!")
            st.audio(audio_data, format="audio/wav")
            
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            st.error(f"Error generating audio: {cancellation_details.reason}")
            if cancellation_details.error_details:
                st.write(f"Details: {cancellation_details.error_details}")
