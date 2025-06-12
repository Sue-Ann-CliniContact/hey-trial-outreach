from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import requests
from bs4 import BeautifulSoup
import re

from matcher import match_studies
from generate_email import generate_outreach_email
from push_to_monday import push_to_monday, fetch_existing_links

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

        condition_keywords = {
            "autism": ["autism", "asd", "autistic"],
            "adhd": ["adhd", "attention deficit"],
            "diabetes": ["diabetes", "insulin"],
            "epilepsy": ["epilepsy", "seizures"],
            "tbi": ["tbi", "traumatic brain injury", "concussion"],
            "brain injury": ["brain injury", "head trauma"],
            "schizophrenia": ["schizophrenia", "psychosis"],
            "ptsd": ["ptsd", "post traumatic stress"],
            "depression": ["depression", "major depressive"],
            "bipolar": ["bipolar"],
            "alzheimers": ["alzheimer", "dementia"],
            "parkinsons": ["parkinson"],
            "cardiac": ["cardiac", "heart failure", "cardiovascular"],
            "obesity": ["obesity", "overweight"],
            "cancer": ["cancer", "oncology", "tumor"],
            "sleep": ["sleep", "insomnia", "sleep apnea"]
        }

        detected_condition = "general"
        for label, keywords in condition_keywords.items():
            if any(kw in text for kw in keywords):
                detected_condition = label
                break

        age_match = re.search(r'ages?\s*(\d+)[\s–\-]+(\d+)', text)
        if age_match:
            min_age = int(age_match.group(1))
            max_age = int(age_match.group(2))
        else:
            min_age = 5
            max_age = 17

        return {
            "condition": detected_condition,
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
            return {"reply": f"Got it. What challenges have you experienced with recruitment for this study?"}
        return {"reply": "Please provide a valid study link."}

    elif state["step"] == 4:
        state["challenge_summary"] = message

        all_matches = match_studies(
            condition=state["condition"],
            campaign_min_age=state["min_age"],
            campaign_max_age=state["max_age"],
            require_contact_email=True,
            challenge_summary=state["challenge_summary"]
        )

        existing_links = fetch_existing_links()
        filtered = []
        for m in all_matches:
            nct_id = m.get("nct_id")
            trial_link = f"https://clinicaltrials.gov/study/{nct_id}"
            if trial_link not in existing_links:
                filtered.append(m)
            else:
                print(f"⏭️ Skipped duplicate match: {trial_link}")

        state["matched_studies"] = filtered
        state["sent_count"] = 0
        state["step"] += 1

    if state["step"] >= 5:
        start = state["sent_count"]
        end = start + 5
        batch = state["matched_studies"][start:end]

        if not batch:
            return {"reply": "✅ No more matches to show. You're all caught up!"}

        replies = []
        for study in batch:
            doc_link = generate_outreach_email(
                study,
                your_study_title=state["study_url"],
                challenge_summary=state["challenge_summary"],
                agent_name=state["agent_name"],
                agent_title=state["agent_title"]
            )
            contact_info = ", ".join(study.get("all_contacts", [study.get("contact_email", "N/A")]))
            push_result = push_to_monday(study, internal_study_name=state["study_url"])
            print(f"✅ Study pushed to Monday: {push_result}")

            match_reason = study.get("match_reason", f"it targets {state['condition']} and overlaps with the age criteria.")

            msg = f"""**{study['title']}**  
📍 {study.get('location', 'Location N/A')}  
📨 {contact_info}  
[View Study](https://clinicaltrials.gov/ct2/show/{study['nct_id']})  
[📄 Download Email]({doc_link})  
➡️ This matched because {match_reason}"""
            replies.append(msg)

        state["sent_count"] += len(batch)

        if state["sent_count"] < len(state["matched_studies"]):
            replies.append("If you'd like to see more matches, type 'load more'.")
        else:
            replies.append("✅ No more matches to show. You're all caught up!")

        return {"reply": "\n\n---\n\n".join(replies)}

    return {"reply": "Unexpected state. Please refresh and try again."}
