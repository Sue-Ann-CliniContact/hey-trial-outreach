import os
import json
import requests
from datetime import date

MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
BOARD_ID = "1999034079"
GROUP_ID = "topics"

HEADERS = {
    "Authorization": MONDAY_API_KEY,
    "Content-Type": "application/json"
}

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
    data = response.json()
    links = set()

    try:
        for item in data["data"]["boards"][0]["items"]:
            for col in item["column_values"]:
                if col["id"] == "link_mkrtn4m6" and col["text"]:
                    links.add(col["text"].strip())
    except Exception as e:
        print("⚠️ Failed to parse existing links:", e)

    return links

def push_to_monday(study, internal_study_name=""):
    existing_links = fetch_existing_links()
    study_link = f"https://clinicaltrials.gov/study/{study['nct_id']}"

    if study_link in existing_links:
        print(f"⏭️ Skipping already pushed study: {study_link}")
        return "Already pushed"

    mutation = """
    mutation ($board_id: Int!, $group_id: String!, $item_name: String!, $column_values: JSON!) {
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
        "board_id": int(BOARD_ID),
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
