# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import requests
from bs4 import BeautifulSoup
import re

from matcher import match_studies
from generate_email import generate_outreach_email
from push_to_monday import push_to_monday

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_memory = {}

def extract_study_criteria_from_url(url: str):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text().lower()

        if any(kw in text for kw in ["autism", "asd", "autistic"]):
            condition = "autism"
        elif any(kw in text for kw in ["adhd", "attention deficit"]):
            condition = "adhd"
        elif "diabetes" in text:
            condition = "diabetes"
        else:
            condition = "general"

        age_match = re.search(r'ages?\s*(\d+)[\s–-]+(\d+)', text)
        if age_match:
            min_age = int(age_match.group(1))
            max_age = int(age_match.group(2))
        else:
            min_age = 5
            max_age = 17

        return {
            "condition": condition,
            "min_age": min_age,
            "max_age": max_age
        }
    except Exception as e:
        print(f"⚠️ Error scraping study URL: {e}")
        return {
            "condition": "general",
            "min_age": 5,
            "max_age": 17
        }

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    message = data.get("message", "").strip()

    if session_id not in session_memory:
        session_memory[session_id] = {
            "step": 0,
            "agent_name": "",
            "agent_title": "",
            "study_url": "",
            "challenge_summary": "",
            "condition": "",
            "min_age": None,
            "max_age": None,
            "matched_studies": [],
            "sent_count": 0
        }

    state = session_memory[session_id]

    if state["step"] == 0:
        state["step"] += 1
        return {"reply": "Hi 👋 Who is the CliniContact outreach agent for this effort?"}

    elif state["step"] == 1:
        state["agent_name"] = message.title()
        state["step"] += 1
        return {"reply": f"What is {state['agent_name']}'s title?"}

    elif state["step"] == 2:
        state["agent_title"] = message.strip()
        state["step"] += 1
        return {"reply": "Great. Please paste the landing page or ClinicalTrials.gov link for the study you're referencing."}

    elif state["step"] == 3:
        if message.startswith("http"):
            state["study_url"] = message
            parsed = extract_study_criteria_from_url(message)
            state["condition"] = parsed["condition"]
            state["min_age"] = parsed["min_age"]
            state["max_age"] = parsed["max_age"]
            state["step"] += 1
            return {"reply": f"Got it. What challenges have you experienced with recruitment for this s
