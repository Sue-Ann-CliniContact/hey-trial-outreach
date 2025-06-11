import json

def load_indexed_studies(path="indexed_studies.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

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
        return True

def match_studies(condition="autism", campaign_min_age=5, campaign_max_age=17, require_contact_email=True):
    studies = load_indexed_studies()
    matches = []

    for s in studies:
        condition_str = s.get("conditions", "").lower()
        if condition.lower() not in condition_str:
            continue
        if not age_overlap(s, campaign_min_age, campaign_max_age):
            continue
        if require_contact_email and not s.get("contact_email"):
            continue

        matches.append({
            "nct_id": s.get("nct_id"),
            "title": s.get("official_title"),
            "summary": s.get("brief_summary"),
            "eligibility": s.get("eligibility", ""),
            "contact_name": s.get("contact_name"),
            "contact_email": s.get("contact_email"),
            "location": s.get("locations", ""),
            "why_match": f"Matched condition: {condition}, overlapping age"
        })

    return matches
