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

def fetch_existing_emails():
    query = f"""
    query GetEmails {{
      boards(ids: {BOARD_ID}) {{
        items_page(limit: 100) {{
          items {{
            id
            name
            column_values {{
              id
              value
            }}
          }}
        }}
      }}
    }}
    """
    response = requests.post("https://api.monday.com/v2", headers=HEADERS, json={"query": query})
    emails = set()

    try:
        data = response.json()
        print("📦 Raw response JSON:", json.dumps(data, indent=2))

        board = data.get("data", {}).get("boards", [{}])[0]
        items = board.get("items_page", {}).get("items", [])
        for item in items:
            for col in item.get("column_values", []):
                if col["id"] == "email_mkrt39hj" and col["value"]:
                    value = col["value"]
                    try:
                        value_data = json.loads(value)
                        email = value_data.get("email", "").strip().lower()
                        if email:
                            emails.add(email)
                    except json.JSONDecodeError:
                        if "@" in value:
                            emails.add(value.strip().lower())
    except Exception as e:
        print("❌ Error parsing Monday.com response for existing emails:", e)
        print("🔎 Raw response:", response.text)

    return emails

def push_to_monday(study, internal_study_name=""):
    contact_email = (study.get("contact_email") or "").strip().lower()
    if not contact_email:
        print("⚠️ Skipping push due to missing email.")
        return None

    existing_emails = fetch_existing_emails()
    if contact_email in existing_emails:
        print(f"⏭️ Skipping already pushed study for email: {contact_email}")
        return "Already pushed"

    mutation = """
    mutation ($board_id: ID!, $group_id: String!, $item_name: String!, $column_values: JSON!) {
      create_item(board_id: $board_id, group_id: $group_id, item_name: $item_name, column_values: $column_values) {
        id
      }
    }
    """

    contact_person = study.get("contact_name", "N/A")
    title = study.get("title", "Untitled")
    summary = study.get("summary", "")
    eligibility = study.get("eligibility_text", "")
    study_link = f"https://clinicaltrials.gov/study/{study['nct_id']}"

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
