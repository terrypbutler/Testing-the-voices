import streamlit as st
import csv
import random
import os
import azure.cognitiveservices.speech as speechsdk

# --- 1. Page Configuration ---
st.set_page_config(page_title="Virtual Classroom Simulator", layout="wide")
st.title("Virtual Student Simulator")
st.write("Interact with distinct student personas powered by Azure Neural Voices.")

# --- 2. Retrieve Credentials ---
AZURE_KEY = st.secrets["azure_speech"]["key"]
AZURE_REGION = st.secrets["azure_speech"]["region"]

# --- 3. Load the Student Roster from CSVs (AUTO-DETECT & FORGIVING MODE) ---
@st.cache_data
def load_roster():
    # Removed the Indian neural voices from both arrays
    female_voices = ["en-GB-MaisieNeural", "en-GB-SoniaNeural", "en-US-JennyNeural", "en-US-JaneNeural", "en-AU-NatashaNeural", "en-CA-ClaraNeural"]
    male_voices = ["en-GB-RyanNeural", "en-GB-ThomasNeural", "en-US-DavisNeural", "en-US-GuyNeural", "en-AU-WilliamNeural", "en-CA-LiamNeural"]
    
    students = []
    
    available_files = [f for f in os.listdir() if f.lower().endswith(('.csv', '.cfv'))]
    year7_file = next((f for f in available_files if '7' in f), None)
    year10_file = next((f for f in available_files if '9' in f or '10' in f), None)
    
    datasets = []
    if year7_file:
        datasets.append({"file": year7_file, "year": "Year 7", "pitch_min": 0, "pitch_max": 15})
    if year10_file:
        datasets.append({"file": year10_file, "year": "Year 10", "pitch_min": -15, "pitch_max": 0})
        
    for dataset in datasets:
        with open(dataset["file"], mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # Clean up the dictionary keys to ignore accidental spaces in the CSV headers
                clean_row = {str(k).strip(): str(v).strip() for k, v in row.items() if k is not None}
                
                # Check for standard column names, or fallback to common variations
                student_id = clean_row.get("Student ID") or clean_row.get("ID") or clean_row.get("UPN")
                
                # If we STILL can't find an ID, skip the row
                if not student_id:
                    continue
                    
                random.seed(student_id)
                
                name = clean_row.get("Full Name") or clean_row.get("Name") or "Unknown Student"
                gender = clean_row.get("Gender", "").upper()
                
                if gender == "M":
                    voice = random.choice(male_voices)
                elif gender == "F":
                    voice = random.choice(female_voices)
                else:
                    voice = random.choice(female_voices + male_voices)
                    
                pitch_val = random.randint(dataset["pitch_min"], dataset["pitch_max"])
                rate_val = random.randint(-10, 10)
                
                # Grab the pedagogical data, forgiving different column names
                portrait = clean_row.get("Transition Portrait") or clean_row.get("Portrait") or ""
                maths_notes = clean_row.get("Maths") or clean_row.get("Math") or ""
                
                students.append({
                    "id": student_id,
                    "name": f"{name} ({dataset['year']})", 
                    "voice": voice,
                    "year_group": dataset["year"], 
                    "default_style": "cheerful",
                    "pitch_adjust": f"+{pitch_val}%" if pitch_val > 0 else f"{pitch_val}%",
                    "rate_adjust": f"+{rate_val}%" if rate_val > 0 else f"{rate_val}%",
                    "misconception": f"[{dataset['year']}] {portrait} MATHS: {maths_notes}"
                })
                
    return students

# Initialize data and dictionary mapping
students_data = load_roster()
roster_dict = {student["name"]: student for student in students_data}

# --- 4. Sidebar: Student Selection & Profile ---
st.sidebar.header("Classroom Roster")

year_filter = st.sidebar.radio(
    "Filter by Year Group",
    ["All", "Year 7", "Year 10"],
    horizontal=True
)

if year_filter == "All":
    filtered_roster = roster_dict
else:
    filtered_roster = {name: data for name, data in roster_dict.items() if data["year_group"] == year_filter}

if not filtered_roster:
    st.sidebar.error(f"No students loaded for {year_filter}. Please check the column names in your CSV file!")
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
if st.button("Generate Voice"):
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
