from docx import Document
from datetime import date
import os

def generate_outreach_email(match, your_study_title, challenge_summary, success_summary="", agent_name="The CliniContact Team", output_folder="emails"):
    """
    match: dict with study match details (from matcher)
    your_study_title: str, title of your original campaign
    challenge_summary: str, 1-2 lines describing the recruitment challenge
    success_summary: str, what CliniContact achieved
    agent_name: str, name of the outreach agent
    """
    os.makedirs(output_folder, exist_ok=True)
    doc = Document()
    doc.add_heading('Personalized Outreach Email', level=1)
    
    doc.add_paragraph(f"Date: {date.today().strftime('%B %d, %Y')}\n")
    doc.add_paragraph(f"Dear {match.get('contact_name', 'Research Team')},\n")

    doc.add_paragraph(f"I’m reaching out regarding your study titled:\n“{match.get('title')}”.")
    
    doc.add_paragraph(f"At CliniContact, we recently supported a similar study, \"{your_study_title}\", which faced the following recruitment challenge:")
    doc.add_paragraph(challenge_summary)

    if success_summary:
        doc.add_paragraph("Here’s what we were able to accomplish:")
        doc.add_paragraph(success_summary)

    doc.add_paragraph("Given the similarities between your study and ours (especially in terms of condition and participant age range), we believe our services could meaningfully accelerate your recruitment goals.")
    
    doc.add_paragraph("We’d love to explore whether we could assist your team in the same way. Please let me know if you’d be open to a quick conversation.")

    doc.add_paragraph(f"Warm regards,\n{agent_name}\ninfo@clinicontact.com")

    # Save the file
    file_name = f"{match.get('nct_id', 'study')}_outreach.docx"
    file_path = os.path.join(output_folder, file_name)
    doc.save(file_path)
    return file_path

# Example usage
if __name__ == "__main__":
    test_match = {
        "nct_id": "NCT12345678",
        "title": "Study of ASD in Children",
        "contact_name": "Dr. Smith"
    }
    path = generate_outreach_email(
        match=test_match,
        your_study_title="Autism Parent Trial – CA 2024",
        challenge_summary="It was challenging to recruit verbal boys under 10 within a 30-mile radius of Fresno.",
        success_summary="We delivered 92 high-intent leads in under 6 weeks using geo-targeted outreach and SMS follow-up.",
        agent_name="Sue-Ann Schmitt"
    )
    print(f"Email saved to: {path}")
