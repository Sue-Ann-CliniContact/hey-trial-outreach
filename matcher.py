import json
from difflib import SequenceMatcher

def load_indexed_studies(path="indexed_studies.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def condition_matches(study_condition, target_condition, threshold=0.6):
    study_condition = study_condition.lower()
    target_condition = target_condition.lower()
    study_tokens = study_condition.split()
    target_tokens = target_condition.split()
    match_score = SequenceMatcher(None, study_condition, target_condition).ratio()

    return (
        any(token in study_condition for token in target_tokens)
        or match_score >= threshold
    )

def age_overlap(study, min_age=None, max_age=None, tolerance=3):
    try:
        study_min = int(study.get("min_age", 0))
        study_max = int(study.get("max_age", 100))
        min_check = (min_age is None or study_max + tolerance >= min_age)
        max_check = (max_age is None or study_min - tolerance <= max_age)
        return min_check and max_check
    except:
        return True  # fallback match

def match_studies(condition="autism", campaign_min_age=5, campaign_max_age=15, top_n=5, require_contact_email=True):
    studies = load_indexed_studies()
    matches = []

    for s in studies:
        study_condition = s.get("condition", "")
        if not condition_matches(study_condition, condition):
            continue

        if not age_overlap(s, campaign_min_age, campaign_max_age):
            continue

        if require_contact_email and not s.get("contact_email"):
            continue

        matches.append(s)

    return matches[:top_n]
