import streamlit as st
from matcher import match_studies
from generate_email import generate_outreach_email
from push_to_monday import push_to_monday
import os

st.set_page_config(page_title="Hey Trial Outreach Matcher", layout="wide")

st.title("🔍 Internal Study Matcher for Outreach")

with st.form("input_form"):
    st.subheader("Your Original Study Details")
    internal_title = st.text_input("Study Title", "Autism CA 2024")
    challenge = st.text_area("What was the recruitment challenge?", height=100)
    success = st.text_area("How did CliniContact solve it?", height=100)
    min_age = st.number_input("Min Age", value=5)
    max_age = st.number_input("Max Age", value=15)
    n_matches = st.slider("How many matches to return", 1, 10, 5)
    submitted = st.form_submit_button("Match & Generate")

if submitted:
    st.info("Matching studies...")
    matches = match_studies(campaign_min_age=min_age, campaign_max_age=max_age, top_n=n_matches)

    if not matches:
        st.warning("No matches found.")
    else:
        for i, match in enumerate(matches, 1):
            st.markdown(f"### Match {i}: {match.get('title')}")
            st.write(f"📄 Summary: {match.get('summary')}")
            st.write(f"👤 Contact: {match.get('contact_name')} | ✉️ {match.get('contact_email')}")
            st.write(f"🔗 [View Study](https://clinicaltrials.gov/ct2/show/{match.get('nct_id')})")

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"📧 Generate Email - Match {i}"):
                    path = generate_outreach_email(
                        match,
                        your_study_title=internal_title,
                        challenge_summary=challenge,
                        success_summary=success
                    )
                    st.success(f"Email created at: {path}")
            with col2:
                if st.button(f"📤 Push to Monday - Match {i}"):
                    push_to_monday(match, internal_study_name=internal_title)
                    st.success("✅ Added to Monday.com")

