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

# --- 3. Load the Student Roster from CSV ---
@st.cache_data
def load_roster():
    female_voices = ["en-GB-MaisieNeural", "en-GB-SoniaNeural", "en-US-JennyNeural", "en-US-JaneNeural", "en-AU-NatashaNeural", "en-CA-ClaraNeural", "en-IN-NeerjaNeural"]
    male_voices = ["en-GB-RyanNeural", "en-GB-ThomasNeural", "en-US-DavisNeural", "en-US-GuyNeural", "en-AU-WilliamNeural", "en-CA-LiamNeural", "en-IN-PrabhatNeural"]
    
    students = []
    
    # Read the uploaded CSV file directly
    with open('year7_data.csv', mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            if not row.get("Student ID", "").strip():
                continue
                
            # Seed the randomizer with the Student ID so their voice never changes between sessions
            random.seed(row["Student ID"])
            
            gender = row.get("Gender", "").strip().upper()
            if gender == "M":
                voice = random.choice(male_voices)
            elif gender == "F":
                voice = random.choice(female_voices)
            else:
                voice = random.choice(female_voices + male_voices)
                
            pitch_val = random.randint(-10, 10)
            rate_val = random.randint(-10, 10)
            
            students.append({
                "id": row["Student ID"],
                "name": row["Full Name"],
                "voice": voice,
                "default_style": "cheerful",
                "pitch_adjust": f"+{pitch_val}%" if pitch_val > 0 else f"{pitch_val}%",
                "rate_adjust": f"+{rate_val}%" if rate_val > 0 else f"{rate_val}%",
                "misconception": f"{row.get('Transition Portrait', '')} MATHS: {row.get('Maths', '')}"
            })
            
    return students

students_data = load_roster()
roster_dict = {student["name"]: student for student in students_data}

# --- 4. Sidebar: Student Selection & Profile ---
st.sidebar.header("Classroom Roster")
selected_name = st.sidebar.selectbox("Select a Student", list(roster_dict.keys()))

active_student = roster_dict[selected_name]

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
    f"What is {active_student['name']} saying?",
    value="I think I understand the first part, but I'm completely lost on what to do next."
)

# --- 6. Generate the Audio ---
if st.button(f"Generate {active_student['name']}'s Voice"):
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
            st.success(f"Audio generated successfully!")
            st.audio(audio_data, format="audio/wav")
            
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            st.error(f"Error generating audio: {cancellation_details.reason}")
            if cancellation_details.error_details:
                st.write(f"Details: {cancellation_details.error_details}")
