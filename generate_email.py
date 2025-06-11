from docx import Document
from datetime import date
import os
import io
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Your shared Google Drive folder ID
FOLDER_ID = "1ruHSgI3jo4rKKrLahitkNzFwGwT3yjCt"

def upload_to_drive(local_path, filename):
    # Load credentials from environment variable instead of file
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive"]
    )

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

def generate_outreach_email(match, your_study_title, challenge_summary, success_summary="", agent_name="The CliniContact Team", output_folder="emails"):
    os.makedirs(output_folder, exist_ok=True)
    doc = Document()
    doc.add_heading('Personalized Outreach Email', level=1)

    doc.add_paragraph(f"Date: {date.today().strftime('%B %d, %Y')}\n")
    doc.add_paragraph(f"Dear {match.get('contact_name', 'Research Team')},\n")

    doc.add_paragraph(f"I’m reaching out regarding your study titled:\n“{match.get('study_title')}”.")
    doc.add_paragraph(f"At CliniContact, we recently supported a similar study, \"{your_study_title}\", which faced the following recruitment challenge:")
    doc.add_paragraph(challenge_summary)

    if success_summary:
        doc.add_paragraph("Here’s what we were able to accomplish:")
        doc.add_paragraph(success_summary)

    doc.add_paragraph("Given the similarities between your study and ours (especially in terms of condition and participant age range), we believe our services could meaningfully accelerate your recruitment goals.")
    doc.add_paragraph("We’d love to explore whether we could assist your team in the same way. Please let me know if you’d be open to a quick conversation.")
    doc.add_paragraph(f"Warm regards,\n{agent_name}\ninfo@clinicontact.com")

    filename = f"{match.get('nct_id', 'study')}_outreach.docx"
    local_path = os.path.join(output_folder, filename)
    doc.save(local_path)

    return upload_to_drive(local_path, filename)
