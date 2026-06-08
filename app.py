from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play
import os
load_dotenv()
elevenlabs = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)
audio = elevenlabs.text_to_speech.convert(
    text="The first move is what sets everything in motion.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",  # "George" - browse voices at elevenlabs.io/app/voice-library
    model_id="eleven_v3",
    output_format="mp3_44100_128",
)
play(audio)

from elevenlabs.core import ApiError
# (Make sure to import your other required modules)

try:
    # Your existing code that generates and plays the audio
    # audio = client.text_to_speech.convert(...)
    play(audio)
except ApiError as e:
    print("--- ElevenLabs API Error ---")
    print(f"Status Code: {e.status_code}")
    print(f"Error Details: {e.body}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
