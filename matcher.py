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
    return any(token in study_condition for token in target_tokens) or match_score >= threshold

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

def extract_demographic_keywords(text):
    text = text.lower()
    keywords = []
    if "african american" in text or "black" in text:
        keywords.append("african american")
        keywords.append("black")
    if "hispanic" in text or "latino" in text:
        keywords.append("hispanic")
        keywords.append("latino")
    if "asian" in text:
        keywords.append("asian")
    if "native american" in text:
        keywords.append("native american")
    if "white" in text:
        keywords.append("white")
    if "men" in text or "males" in text:
        keywords.append("male")
    if "women" in text or "females" in text:
        keywords.append("female")
    if "older" in text or "seniors" in text:
        keywords.append("aged 50")
        keywords.append("elderly")
    if "children" in text or "kids" in text:
        keywords.append("children")
        keywords.append("minors")
    return keywords

def demographic_match_score(text, keywords):
    text = text.lower()
    score = 0
    matched_keywords = []
    for kw in keywords:
        if kw in text:
            matched_keywords.append(kw)
            score += 1
    return score, matched_keywords

def match_studies(condition="autism", campaign_min_age=5, campaign_max_age=15, top_n=5, require_contact_email=True, challenge_summary=""):
    studies = load_indexed_studies()
    matches = []

    target_keywords = extract_demographic_keywords(challenge_summary)
    print(f"📌 Extracted demographic keywords from challenge summary: {target_keywords}")

    for s in studies:
        match_reason = []

        study_condition = s.get("condition") or s.get("study_title") or s.get("summary", "")
        if not condition_matches(study_condition, condition):
            continue
        match_reason.append("condition match")

        if not age_overlap(s, campaign_min_age, campaign_max_age):
            continue
        match_reason.append("age overlap")

        if require_contact_email and not s.get("contact_email"):
            continue

        if "title" not in s:
            s["title"] = s.get("study_title") or s.get("condition") or "Untitled Study"

        eligibility_text = s.get("eligibility_text", "") + " " + s.get("summary", "")
        demo_score, demo_terms = demographic_match_score(eligibility_text, target_keywords)
        s["demographic_score"] = demo_score
        if demo_score > 0:
            match_reason.append(f"mentions {', '.join(demo_terms)}")

        s["match_reason"] = "; ".join(match_reason)

        print(f"→ {s['title']} matched with score {demo_score} based on: {match_reason}")
        matches.append(s)

    matches = sorted(matches, key=lambda x: x.get("demographic_score", 0), reverse=True)
    return matches[:top_n]
