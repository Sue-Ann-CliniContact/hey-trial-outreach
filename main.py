from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from matcher import match_studies
from generate_email import generate_outreach_email
from push_to_monday import push_to_monday

app = FastAPI()

# CORS: Allow Webflow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify domain like "https://www.clinicontact.com"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store session data in memory (simple version)
session_memory = {}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    message = data.get("message", "").strip()

    if session_id not in session_memory:
        session_memory[session_id] = {
            "step": 0,
            "title": "",
            "challenge": "",
            "solution": "",
            "min_age": 5,
            "max_age": 15
        }

    state = session_memory[session_id]

    # Step-by-step prompt logic
    if state["step"] == 0:
        state["step"] += 1
        return {"reply": "What is the title of the study you'd like to reference?"}
    elif state["step"] == 1:
        state["title"] = message
        state["step"] += 1
        return {"reply": "What was the biggest challenge with recruitment?"}
    elif state["step"] == 2:
        state["challenge"] = message
        state["step"] += 1
        return {"reply": "How did CliniContact help overcome this challenge?"}
    elif state["step"] == 3:
        state["solution"] = message
        state["step"] += 1
        return {"reply": "Great — what age range were you targeting? (e.g. 5–15)"}
    elif state["step"] == 4:
        try:
            parts = [int(x.strip()) for x in message.replace("to", "–").replace("-", "–").split("–")]
            state["min_age"], state["max_age"] = parts[0], parts[1]
        except:
            return {"reply": "Sorry, please provide the age range like this: 5–15"}
        state["step"] += 1

        # Match studies
        matches = match_studies(
            campaign_min_age=state["min_age"],
            campaign_max_age=state["max_age"],
            top_n=5
        )

        if not matches:
            return {"reply": "No matches found based on the info provided."}

        # Pick first match and generate email
        selected = matches[0]
        push_to_monday(selected, state["title"])
        doc_path = generate_outreach_email(
            selected,
            your_study_title=state["title"],
            challenge_summary=state["challenge"],
            success_summary=state["solution"]
        )

        return {
            "reply": f"""Here’s a match I found based on your study **{state['title']}**:\n
**{selected['title']}**  
[View Study](https://clinicaltrials.gov/ct2/show/{selected['nct_id']})  
Contact: {selected.get("contact_name", "N/A")}  
Email: {selected.get("contact_email", "N/A")}

✅ I’ve pushed this to Monday.com and generated an outreach email [📄 Download]({doc_path})"""
        }

    else:
        return {"reply": "You're all set! Refresh to start a new session."}

