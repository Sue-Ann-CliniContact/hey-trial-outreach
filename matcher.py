import json
import re
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

def extract_age_from_text(text):
    text = text.lower()
    age_matches = re.findall(r"(?:aged|age|ages|participants aged)\s*(\d{1,3})\s*(?:to|–|-|through|and)\s*(\d{1,3})", text)
    if age_matches:
        try:
            return int(age_matches[0][0]), int(age_matches[0][1])
        except:
            return None, None
    age_single = re.findall(r"aged?\s*(\d{1,3})\s*(?:\+|and up|or older)", text)
    if age_single:
        try:
            return int(age_single[0]), 100
        except:
            return None, None
    return None, None

def age_overlap(study, min_age=None, max_age=None, tolerance=3):
    try:
        study_min = study.get("min_age_years")
        study_max = study.get("max_age_years")

        if study_min is None or study_max is None:
            text = study.get("eligibility_text", "")
            study_min, study_max = extract_age_from_text(text)

        study_min = study_min if study_min is not None else 0
        study_max = study_max if study_max is not None else 100

        min_check = (min_age is None or study_max + tolerance >= min_age)
        max_check = (max_age is None or study_min - tolerance <= max_age)
        return min_check and max_check
    except:
        return True  # fallback match

def match_studies(condition="autism", campaign_min_age=5, campaign_max_age=15, top_n=5, require_contact_email=True):
    studies = load_indexed_studies()
    matches = []

    for s in studies:
        study_condition = s.get("condition") or s.get("study_title") or s.get("summary", "")
        if not condition_matches(study_condition, condition):
            continue

        if not age_overlap(s, campaign_min_age, campaign_max_age):
            continue

        if require_contact_email and not s.get("contact_email"):
            continue

        # ✅ Ensure 'title' field is always present
        if "title" not in s:
            s["title"] = s.get("study_title") or s.get("condition") or "Untitled Study"

        matches.append(s)

    return matches[:top_n]