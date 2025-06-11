from docx import Document
from datetime import date
import os
import io
import json
import base64

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

FOLDER_ID = "1ruHSgI3jo4rKKrLahitkNzFwGwT3yjCt"

def upload_to_drive(local_path, filename):
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        raise ValueError("Missing GOOGLE_CREDENTIALS_JSON environment variable.")

    creds_dict = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/drive"])
    service = build("drive", "v3", credentials=credentials)

    file_metadata = {
        "name": filename,
        "parents": [FOLDER_ID]
    }

    with open(local_path, "rb") as f:
        media = MediaIoBaseUpload(f, mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        uploaded = service.files().create(body=file_metadata, media_body=media, fields="id").execute()

    file_id = uploaded.get("id")
    service.permissions().create(fileId=file_id, body={"role": "reader", "type": "anyone"}).execute()
    return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

def generate_outreach_email(match, your_study_title, challenge_summary, success_summary="", agent_name="CliniContact", agent_title="", output_folder="emails"):
    os.makedirs(output_folder, exist_ok=True)
    doc = Document()
    doc.add_heading("Personalized Outreach Email", level=1)

    today = date.today().strftime('%B %d, %Y')
    doc.add_paragraph(f"Date: {today}\n")

    contact = match.get('contact_name', 'Research Team')
    doc.add_paragraph(f"Subject: Potential Collaboration on {match.get('study_title', 'your study')}\n")
    doc.add_paragraph(f"Dear {contact},\n")

    doc.add_paragraph(
        f"My name is {agent_name}, and I work as a {agent_title} at CliniContact, where we support clinical researchers in participant recruitment."
    )

    doc.add_paragraph(
        f"I came across your study titled “{match.get('study_title')}”, and it immediately caught my attention due to its alignment with a recent campaign we supported: {your_study_title}."
    )

    doc.add_paragraph("The recruitment challenge we faced in that study was:")
    doc.add_paragraph(challenge_summary)

    if success_summary:
        doc.add_paragraph("Here’s what we accomplished:")
        doc.add_paragraph(success_summary)

    doc.add_paragraph(
        "Because your study appears to target a similar population in terms of condition and age range, I believe we could offer targeted recruitment strategies that would meaningfully accelerate your enrollment goals."
    )

    doc.add_paragraph(
        "Would you be open to a short exploratory conversation to discuss how we can help?"
    )

    filename = f"{match.get('nct_id', 'study')}_outreach.docx"
    local_path = os.path.join(output_folder, filename)
    doc.save(local_path)

    return upload_to_drive(local_path, filename)
