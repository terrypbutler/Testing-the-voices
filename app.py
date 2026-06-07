# --- 3. Load the Student Roster from CSVs ---
@st.cache_data
def load_roster():
    female_voices = ["en-GB-MaisieNeural", "en-GB-SoniaNeural", "en-US-JennyNeural", "en-US-JaneNeural", "en-AU-NatashaNeural", "en-CA-ClaraNeural", "en-IN-NeerjaNeural"]
    male_voices = ["en-GB-RyanNeural", "en-GB-ThomasNeural", "en-US-DavisNeural", "en-US-GuyNeural", "en-AU-WilliamNeural", "en-CA-LiamNeural", "en-IN-PrabhatNeural"]
    
    students = []
    
    # Define the files and their specific pitch boundaries for age simulation
    datasets = [
        {"file": "Virtual_Students - Year 7.csv", "year": "Year 7", "pitch_min": 0, "pitch_max": 15},
        {"file": "Virtual_Students - Year 10.csv", "year": "Year 10", "pitch_min": -15, "pitch_max": 0}
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
                        "default_style": "cheerful",
                        "pitch_adjust": f"+{pitch_val}%" if pitch_val > 0 else f"{pitch_val}%",
                        "rate_adjust": f"+{rate_val}%" if rate_val > 0 else f"{rate_val}%",
                        "misconception": f"[{dataset['year']}] {row.get('Transition Portrait', '')} MATHS: {row.get('Maths', '')}"
                    })
        except FileNotFoundError:
            st.warning(f"Could not find {dataset['file']}. Please ensure it is uploaded to GitHub.")
            
    return students
