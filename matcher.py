import json
from push_to_monday import push_to_monday

def load_indexed_studies(path="indexed_studies.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def is_autism_related(condition: str) -> bool:
    keywords = ["autism", "asd", "autistic", "pervasive developmental"]
    return any(k in condition.lower() for k in keywords)

def age_overlap(study, min_age=None, max_age=None):
    try:
        study_min = int(study.get("min_age", 0))
        study_max = int(study.get("max_age", 100))
        if min_age is not None and study_max < min_age:
            return False
        if max_age is not None and study_min > max_age:
            return False
        return True
    except:
        return True  # fallback to match

def match_studies(campaign_condition="autism", campaign_min_age=5, campaign_max_age=15, top_n=5):
    studies = load_indexed_studies()
    matches = []

    for s in studies:
        condition = s.get("conditions", "")
        if not is_autism_related(condition):
            continue
        if not age_overlap(s, campaign_min_age, campaign_max_age):
            continue
        matches.append({
            "nct_id": s.get("nct_id"),
            "title": s.get("official_title"),
            "summary": s.get("brief_summary"),
            "eligibility": s.get("eligibility", ""),
            "contact_name": s.get("contact_name"),
            "contact_email": s.get("contact_email"),
            "location": s.get("locations", ""),
            "why_match": "Similar age range and autism-related condition"
        })

    return matches[:top_n]

if __name__ == "__main__":
    print("🔍 Finding matches...")
    matched_studies = match_studies(campaign_min_age=5, campaign_max_age=15, top_n=5)

    internal_study_name = "Autism CA 2024"
    if not matched_studies:
        print("⚠️ No matches found.")
    else:
        print(f"✅ Found {len(matched_studies)} matches. Pushing to Monday.com...")
        for match in matched_studies:
            push_to_monday(match, internal_study_name=internal_study_name)
