import csv
import json
import random

# 1. Base Voice Pools mapped by Gender
female_voices = [
    "en-GB-MaisieNeural", "en-GB-SoniaNeural", "en-US-JennyNeural", 
    "en-US-JaneNeural", "en-AU-NatashaNeural", "en-CA-ClaraNeural", "en-IN-NeerjaNeural"
]

male_voices = [
    "en-GB-RyanNeural", "en-GB-ThomasNeural", "en-US-DavisNeural", 
    "en-US-GuyNeural", "en-AU-WilliamNeural", "en-CA-LiamNeural", "en-IN-PrabhatNeural"
]

def convert_csv_to_json(csv_filepath, json_filepath):
    students = []
    
    with open(csv_filepath, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # Skip any empty rows
            if not row["Student ID"].strip():
                continue
                
            # Assign a random voice from the correct gender pool
            gender = row["Gender"].strip().upper()
            if gender == "M":
                voice = random.choice(male_voices)
            elif gender == "F":
                voice = random.choice(female_voices)
            else:
                # Fallback or Non-Binary (e.g., Rowan L.)
                voice = random.choice(female_voices + male_voices)
                
            # Randomize prosody slightly (-10% to +10%)
            pitch_val = random.randint(-10, 10)
            rate_val = random.randint(-10, 10)
            pitch_str = f"+{pitch_val}%" if pitch_val > 0 else f"{pitch_val}%"
            rate_str = f"+{rate_val}%" if rate_val > 0 else f"{rate_val}%"
            
            # Combine the transition portrait and math notes into the profile
            # You can customize this to include English, SEN status, etc.
            pedagogical_notes = f"{row['Transition Portrait']} MATHS: {row['Maths']}"
            
            student_profile = {
                "id": row["Student ID"],
                "name": row["Full Name"],
                "voice": voice,
                "default_style": "cheerful",  # You could map this based on SEN or portrait keywords!
                "pitch_adjust": pitch_str,
                "rate_adjust": rate_str,
                "misconception": pedagogical_notes
            }
            students.append(student_profile)
            
    # Save the JSON file
    with open(json_filepath, mode='w', encoding='utf-8') as outfile:
        json.dump({"students": students}, outfile, indent=2)
        
    print(f"Successfully generated {len(students)} students in {json_filepath}!")

# 3. Execute the script
convert_csv_to_json('year7_data.csv', 'students.json')
