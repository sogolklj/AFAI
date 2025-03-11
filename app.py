from fastapi import FastAPI, UploadFile, File
import pandas as pd
import json
import requests
import openai
import io

app = FastAPI()

# OpenAI API Key (Set in GitHub Secrets)
OPENAI_API_KEY = "your_api_key_here"

# JSON File URLs (Stored in GitHub)
JSON_URLS = {
    "symptom_decision": "https://raw.githubusercontent.com/yourusername/AF-Management-AI/main/symptom_decision.json",
    "rate_control": "https://raw.githubusercontent.com/yourusername/AF-Management-AI/main/rate_control.json",
    "rhythm_control": "https://raw.githubusercontent.com/yourusername/AF-Management-AI/main/rhythm_control.json",
    "ecg_parameters": "https://raw.githubusercontent.com/yourusername/AF-Management-AI/main/ecg_parameters.json",
    "lifestyle_recommendations": "https://raw.githubusercontent.com/yourusername/AF-Management-AI/main/af_management_recommendations.json"
}

# Function to fetch JSON guidelines from GitHub
def fetch_json(url):
    response = requests.get(url)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None

# Load all JSON decision rules
json_rules = {key: fetch_json(url) for key, url in JSON_URLS.items()}

# AI Processing Function
def analyze_with_gpt(patient_data):
    patient_info = json.dumps(patient_data, indent=4)

    prompt_text = f"""
    You are an AI cardiologist specializing in atrial fibrillation (AF) management.
    Analyze the patient data and apply JSON-based clinical rules.

    Patient Data:
    {patient_info}

    Clinical Guidelines:
    {json.dumps(json_rules, indent=4)}

    Generate an AF management plan including:
    - Anticoagulation Strategy
    - Rate Control (Symptoms, Medications, Adjustments)
    - Rhythm Control (ECG, LVEF, Medication Adjustments)
    - Medication Table
    - Lifestyle & Comorbidities Management
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are an AI cardiologist."},
                  {"role": "user", "content": prompt_text}],
        max_tokens=1000
    )

    return response['choices'][0]['message']['content']

@app.post("/upload/")
async def upload_excel(file: UploadFile = File(...)):
    contents = await file.read()
    excel_data = pd.read_excel(io.BytesIO(contents))

    if "patient_ID" not in excel_data.columns or "visit_ID" not in excel_data.columns:
        return {"error": "Missing patient_ID or visit_ID"}

    patient_data = excel_data.iloc[0].to_dict()
    management_plan = analyze_with_gpt(patient_data)

    return {"patient_ID": patient_data["patient_ID"], "visit_ID": patient_data["visit_ID"], "management_plan": management_plan}
