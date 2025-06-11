import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load .env if local
load_dotenv()

MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
BOARD_ID = "1987448172"  # Fixed type from Int to ID (string)
GROUP_ID = "topics"

HEADERS = {
    "Authorization": MONDAY_API_KEY,
    "Content-Type": "application/json"
}

COLUMN_MAPPING = {
    "name": "name",
    "date": "date4",
    "study_title": "text_mkrtxgyc",
    "study_summary": "long_text_mkrtn4eb",
    "eligibility": "long_text_mkrtc9jf",
    "nct_link": "link_mkrtn4m6",
    "contact_name": "text_mkrtjwn9",
    "contact_email": "email_mkrt39hj"
}

def push_to_monday(match, internal_study_name="CliniContact Campaign"):
    column_values = {
        COLUMN_MAPPING["date"]: datetime.utcnow().strftime("%Y-%m-%d"),
        COLUMN_MAPPING["study_title"]: match.get("title", ""),
        COLUMN_MAPPING["study_summary"]: match.get("summary", ""),
        COLUMN_MAPPING["eligibility"]: match.get("eligibility", ""),
        COLUMN_MAPPING["nct_link"]: {
            "url": f"https://clinicaltrials.gov/ct2/show/{match.get('nct_id', '')}",
            "text": "View Study"
        },
        COLUMN_MAPPING["contact_name"]: match.get("contact_name", ""),
        COLUMN_MAPPING["contact_email"]: match.get("contact_email", "")
    }

    mutation = {
        "query": """
        mutation ($board_id: ID!, $group_id: String!, $item_name: String!, $column_values: JSON!) {
          create_item (
            board_id: $board_id,
            group_id: $group_id,
            item_name: $item_name,
            column_values: $column_values
          ) {
            id
          }
        }
        """,
        "variables": {
            "board_id": BOARD_ID,
            "group_id": GROUP_ID,
            "item_name": internal_study_name,
            "column_values": column_values
        }
    }

    response = requests.post("https://api.monday.com/v2", headers=HEADERS, json=mutation)

    if response.status_code == 200:
        print(f"✅ Study pushed to Monday: {match.get('title')}")
    else:
        print(f"❌ Error pushing to Monday:")
        print(response.text)

# Optional test run
if __name__ == "__main__":
    sample = {
        "nct_id": "NCT55555555",
        "title": "Autism Behavior Therapy Study",
        "summary": "Testing parent-led CBT interventions in ASD youth.",
        "eligibility": "Ages 8–16, formal ASD diagnosis, must attend weekly sessions.",
        "contact_name": "Dr. Sarah Clinical",
        "contact_email": "s.clinical@example.edu"
    }
    push_to_monday(sample, internal_study_name="Autism CA 2024")
