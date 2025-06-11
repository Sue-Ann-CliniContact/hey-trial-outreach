from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from matcher import match_studies
from generate_email import generate_outreach_email
from push_to_monday import push_to_monday

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_memory = {}

# --------- Placeholder for condition extractor from landing page ---------
def extract_study_criteria_from_url(url: str):
    # TODO: Replace with real HTML parsing / scraping
    return {
        "condition": "autism",
        "min_age": 5,
        "max_age": 17
    }

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    message = data.get("message", "").strip().lower()

    if session_id not in session_memory:
        session_memory[session_id] = {
            "step": 0,
            "agent_name": "",
            "study_url": "",
            "challenge_summary": "",
            "condition": "",
            "min_age": None,
            "max_age": None,
            "matched_studies": [],
            "sent_count": 0
        }

    state = session_memory[session_id]

    # Conversation flow
    if state["step"] == 0:
        state["step"] += 1
        return {"reply": "Hi 👋 Who is the CliniContact outreach agent for this effort?"}

    elif state["step"] == 1:
        state["agent_name"] = message.title()
        state["step"] += 1
        return {"reply": "Great. Please paste the landing page or ClinicalTrials.gov link for the study you're referencing."}

    elif state["step"] == 2:
        state["study_url"] = message
        parsed = extract_study_criteria_from_url(message)
        state["condition"] = parsed["condition"]
        state["min_age"] = parsed["min_age"]
        state["max_age"] = parsed["max_age"]
        state["step"] += 1
        return {"reply": f"Got it. What challenges have you experienced with recruitment for this study?"}

    elif state["step"] == 3:
        state["challenge_summary"] = message
        # Perform match
        matches = match_studies(
            condition=state["condition"],
            campaign_min_age=state["min_age"],
            campaign_max_age=state["max_age"],
            require_contact_email=True
        )
        state["matched_studies"] = matches
        state["sent_count"] = 0
        state["step"] += 1

    # Return 5 matches at a time
    if state["step"] >= 4:
        if "load more" in message:
            pass  # continue to load more
        elif state["sent_count"] > 0:
            return {"reply": "If you'd like to see more matches, type 'load more'."}

        start = state["sent_count"]
        end = start + 5
        batch = state["matched_studies"][start:end]

        if not batch:
            return {"reply": "✅ No more matches to show. You're all caught up!"}

        replies = []
        for study in batch:
            # Push to Monday and generate email
            push_to_monday(study, state["study_url"])
            doc_link = generate_outreach_email(
                study,
                your_study_title=state["study_url"],
                challenge_summary=state["challenge_summary"],
                agent_name=state["agent_name"]
            )
            msg = f"""**{study['title']}**  
📍 {study.get('location', 'Location N/A')}  
📨 {study.get('contact_email', 'Email N/A')}  
[View Study](https://clinicaltrials.gov/ct2/show/{study['nct_id']})  
[📄 Download Email]({doc_link})  
➡️ This matched because it's also targeting **{state['condition']}** and has overlapping age criteria."""
            replies.append(msg)

        state["sent_count"] += len(batch)
        return {"reply": "\n\n---\n\n".join(replies)}

    return {"reply": "Unexpected state. Please refresh and try again."}
