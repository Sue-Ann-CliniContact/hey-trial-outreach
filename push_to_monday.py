import os
import json
import requests
from datetime import date
import re

MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
BOARD_ID = "1999034079"
GROUP_ID = "topics"

HEADERS = {
    "Authorization": MONDAY_API_KEY,
    "Content-Type": "application/json"
}

def extract_nct_id(link):
    match = re.search(r'(NCT\d{8})', link)
    return match.group(1) if match else None

def fetch_existing_links():
    query = f"""
    query {{
      boards(ids: {BOARD_ID}) {{
        items {{
          column_values {{
            id
            text
          }}
        }}
      }}
    }}
    """
    response = requests.post("https://api.monday.com/v2", headers=HEADERS, json={"query": query})
    links = set()

    try:
        data = response.json()
        items = data.get("data", {}).get("boards", [{}])[0].get("items", [])
        for item in items:
            for col in item.get("column_values", []):
                if col["id"] == "link_mkrtn4m6" and col["text"]:
                    nct_id = extract_nct_id(col["text"].strip())
                    if nct_id:
                        links.add(nct_id)
    except Exception as e:
        print("❌ Error parsing Monday.com response for existing links:", e)
        print("🔎 Raw response:", response.text)

    return links

def push_to_monday(study, internal_study_name=""):
    existing_nct_ids = fetch_existing_links()
    study_nct_id = study["nct_id"]

    if study_nct_id in existing_nct_ids:
        print(f"⏭️ Skipping already pushed study: {study_nct_id}")
        return "Already pushed"

    mutation = """
    mutation ($board_id: ID!, $group_id: String!, $item_name: String!, $column_values: JSON!) {
      create_item(board_id: $board_id, group_id: $group_id, item_name: $item_name, column_values: $column_values) {
        id
      }
    }
    """

    contact_email = study.get("contact_email", "")
    contact_person = study.get("contact_name", "N/A")
    title = study.get("title", "Untitled")
    summary = study.get("summary", "")
    eligibility = study.get("eligibility_text", "")
    study_link = f"https://clinicaltrials.gov/study/{study_nct_id}"

    column_values = {
        "text_mkrtxgyc": title,
        "long_text_mkrtn4eb": {"text": summary},
        "long_text_mkrtc9jf": {"text": eligibility},
        "link_mkrtn4m6": {"url": study_link, "text": study_link},
        "text_mkrtjwn9": contact_person,
        "email_mkrt39hj": {"email": contact_email, "text": contact_email},
        "date4": {"date": date.today().isoformat()}
    }

    variables = {
        "board_id": BOARD_ID,
        "group_id": GROUP_ID,
        "item_name": internal_study_name or title,
        "column_values": json.dumps(column_values)
    }

    response = requests.post("https://api.monday.com/v2", headers=HEADERS, json={"query": mutation, "variables": variables})
    data = response.json()

    if "errors" in data:
        print("❌ Monday.com error:", data["errors"])
        return None

    return title
