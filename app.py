import streamlit as st
import json
import azure.cognitiveservices.speech as speechsdk

# --- 1. Page Configuration ---
st.set_page_config(page_title="Virtual Classroom Simulator", layout="wide")
st.title("Virtual Student Simulator")
st.write("Interact with distinct student personas powered by Azure Neural Voices.")

# --- 2. Retrieve Credentials ---
AZURE_KEY = st.secrets["azure_speech"]["key"]
AZURE_REGION = st.secrets["azure_speech"]["region"]

# --- 3. Load the Student Roster ---
@st.cache_data
def load_roster():
    with open('students.json', 'r') as file:
        return json.load(file)["students"]

students_data = load_roster()

# Create a dictionary to easily look up a student by their name
roster_dict = {student["name"]: student for student in students_data}

# --- 4. Sidebar: Student Selection & Profile ---
st.sidebar.header("Classroom Roster")
selected_name = st.sidebar.selectbox("Select a Student", list(roster_dict.keys()))

# Get the active student's full profile
active_student = roster_dict[selected_name]

# Display their pedagogical profile so the trainee knows who they are dealing with
st.sidebar.subheader("Pedagogical Profile")
st.sidebar.info(active_student.get("misconception", "No notes provided."))
st.sidebar.caption(f"Voice: {active_student['voice']} | Pitch: {active_student['pitch_adjust']} | Rate: {active_student['rate_adjust']}")

# Allow overriding the student's default emotion for testing
current_emotion = st.sidebar.selectbox(
    "Current Emotional State",
    ["cheerful", "sad", "fearful", "angry", "whispering", "excited"],
    index=["cheerful", "sad", "fearful", "angry", "whispering", "excited"].index(active_student.get("default_style", "cheerful"))
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
        
        # Configure Azure Speech Stream
        speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
        pull_stream = speechsdk.audio.PullAudioOutputStream()
        stream_config = speechsdk.audio.AudioOutputConfig(stream=pull_stream)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=stream_config)
        
        # Construct the dynamic SSML payload using the JSON data
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
        
        # Execute synthesis
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
