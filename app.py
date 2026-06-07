import streamlit as st
import azure.cognitiveservices.speech as speechsdk

# 1. Page Configuration
st.title("Virtual Student Voice Sandbox")
st.write("Test different student personas and emotional styles using Azure Speech Services.")

# 2. Retrieve Credentials Securely
AZURE_KEY = st.secrets["azure_speech"]["key"]
AZURE_REGION = st.secrets["azure_speech"]["region"]

# 3. Setup Voice Map (You can expand this up to 70 student names)
student_voices = {
    "Ryan (UK - Standard/Calm)": "en-GB-RyanNeural",
    "Sonia (UK - Expressive)": "en-GB-SoniaNeural",
    "Jenny (US - Conversational)": "en-US-JennyNeural",
    "Guy (US - Expressive)": "en-US-GuyNeural"
}

# 4. Sidebar Controls for the Persona
st.sidebar.header("Student Persona Settings")
selected_student = st.sidebar.selectbox("Select Student Profile", list(student_voices.keys()))
voice_name = student_voices[selected_student]

emotion_style = st.sidebar.selectbox(
    "Select Emotional State",
    ["cheerful", "sad", "fearful", "angry", "whispering", "excited"]
)

intensity = st.sidebar.slider("Emotion Intensity", min_value=0.5, max_value=2.0, value=1.0, step=0.1)

# 5. Main Text Input Area
text_input = st.text_area(
    "What should the student say?",
    value="I am trying my best with this assignment, but some parts are still confusing."
)

# 6. Audio Generation Trigger
if st.button("Generate Student Voice"):
    with st.spinner("Synthesizing speech..."):
        
        # Configure Azure Speech
        speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
        
        # We use a PullAudioOutputStream to catch the bytes in memory
        pull_stream = speechsdk.audio.PullAudioOutputStream()
        stream_config = speechsdk.audio.AudioOutputConfig(stream=pull_stream)
        
        # Pass the stream_config directly into the synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=stream_config)
        
        # Construct the dynamic SSML payload matching the sidebar configurations
        ssml_payload = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='en-GB'>
            <voice name='{voice_name}'>
                <mstts:express-as style='{emotion_style}' styledegree='{intensity}'>
                    {text_input}
                </mstts:express-as>
            </voice>
        </speak>
        """
        
        # Execute synthesis
        result = synthesizer.speak_ssml_async(ssml_payload).get()
        
        # 7. Check Results and Stream to UI Player
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # Read the raw audio bytes out of the stream memory buffer
            audio_data = result.audio_data
            
            st.success(f"Generated output for {selected_student}!")
            # Render the native HTML5 audio player in the user's browser
            st.audio(audio_data, format="audio/wav")
            
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            st.error(f"Error generating audio: {cancellation_details.reason}")
            if cancellation_details.error_details:
                st.write(f"Details: {cancellation_details.error_details}")
