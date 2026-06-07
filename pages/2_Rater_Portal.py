"""
BOARDS-AI — Expert Rater Portal
=================================
Paginated survey form for expert benchmarking of LLM-generated OSCE sessions.
Mirrors the production ``app.py`` rater interface using ``streamlit-survey``.

Ratings are saved as JSON files to the local ``ratings/`` directory.
"""

import streamlit as st
import streamlit_survey as ss
import json
import os
import random
from datetime import datetime, timezone

from case_loader import load_case_by_uid, extract_case_fields
from image_utils import process_images

st.set_page_config(page_title="Rater Portal", page_icon="📋", layout="wide")

RATINGS_DIR = "ratings"
os.makedirs(RATINGS_DIR, exist_ok=True)

# ── Helpers ─────────────────────────────────────────────────────────────────

def normalize_model_name(name: str) -> str:
    """Standardize model name strings to handle historical formatting mismatches."""
    normalized = "".join(c for c in name.lower() if c.isalnum())
    if "llama" in normalized:
        return "llama"
    if "gpt4" in normalized:
        return "gpt4"
    if "claude" in normalized:
        return "claude"
    if "gemini" in normalized:
        return "gemini"
    return normalized


# ── Session State ───────────────────────────────────────────────────────────

if "rater_survey_key" not in st.session_state:
    st.session_state.rater_survey_key = 0
if "rater_session" not in st.session_state:
    st.session_state.rater_session = None
if "rater_name" not in st.session_state:
    st.session_state.rater_name = "Rater 1"
if "last_saved_rating" not in st.session_state:
    st.session_state.last_saved_rating = None
if "last_saved_filename" not in st.session_state:
    st.session_state.last_saved_filename = None
if "all_rated" not in st.session_state:
    st.session_state.all_rated = False


# ── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("📋 Rater Configuration")

    # =========================================================================
    # PRODUCTION SIMPLE LOGIN PAGE CODE (COMMENTED)
    # =========================================================================
    # In production, we used a simple login system by hardcoding credentials 
    # in `.streamlit/secrets.toml`. Here is how you can set it up:
    #
    # 1. In `.streamlit/secrets.toml`, define the credentials:
    #    [passwords]
    #    "rater1@example.com" = "securepass1"
    #    "rater2@example.com" = "securepass2"
    #    "rater3@example.com" = "securepass3"
    #
    # 2. In your app, implement the login form:
    #    if "authenticated" not in st.session_state:
    #        st.session_state.authenticated = False
    #
    #    if not st.session_state.authenticated:
    #        st.header("🔑 Rater Sign In")
    #        email = st.text_input("Email ID")
    #        password = st.text_input("Password", type="password")
    #        if st.button("Sign In"):
    #            secrets_pass = st.secrets.get("passwords", {})
    #            if email in secrets_pass and secrets_pass[email] == password:
    #                st.session_state.authenticated = True
    #                st.session_state.rater_name = email.split("@")[0].replace("rater", "Rater ").strip()
    #                st.rerun()
    #            else:
    #                st.error("Invalid email or password.")
    #        st.stop()
    # =========================================================================

    rater_name = "Rater 1"
    st.session_state.rater_name = rater_name
    st.info(f"Rater: **{rater_name}**")

    st.divider()

    # Count unique existing ratings
    rated_sessions = set()
    if os.path.exists(RATINGS_DIR):
        for fname in os.listdir(RATINGS_DIR):
            if fname.endswith(".json"):
                fpath = os.path.join(RATINGS_DIR, fname)
                try:
                    with open(fpath, "r") as f:
                        data = json.load(f)
                        uid = data.get("uid")
                        model = data.get("model")
                        if uid is not None and model is not None:
                            rated_sessions.add((int(uid), normalize_model_name(str(model))))
                except Exception:
                    pass

    # Count total available sessions in the database
    total_sessions = 0
    db_file = "data/db.osce_qa.json"
    if os.path.exists(db_file):
        try:
            with open(db_file, "r") as f:
                db_data = json.load(f)
            for doc in db_data:
                total_sessions += len(doc.get("session_data", []))
        except Exception:
            pass

    if total_sessions > 0:
        st.metric("Completed Ratings", f"{len(rated_sessions)} / {total_sessions}")
    else:
        st.metric("Completed Ratings", len(rated_sessions))


# ── Helper: tooltip text for each metric ────────────────────────────────────

CLARITY_HELP = """\
**Very Unclear (1):** What's the deal with the lung thing in the picture?

**Unclear (2):** The CT scan shows something in the lung. What's your diagnosis?

**Neutral (3):** A patient's chest CT reveals a pulmonary nodule. What's the most likely diagnosis?

**Clear (4):** A 60-year-old male smoker's chest CT shows a 2 cm spiculated nodule in the right upper lobe. What is the most appropriate next step?

**Very Clear (5):** A 60-year-old male with a 40 pack-year smoking history undergoes a routine chest CT. It reveals a 2 cm spiculated nodule in the right upper lobe, with no calcifications or fat content. The patient is asymptomatic. What is the most appropriate next step in management?

Also consider options while rating.
"""

RELEVANCE_HELP = """\
**Not Relevant (1):** "What is the atomic number of iodine used in CT contrast agents?"

**Slightly Relevant (2):** "What is the k-edge of iodine used in CT contrast agents?"

**Moderately Relevant (3):** "What is the typical concentration of iodine (in mg/mL) used in CT contrast agents for abdominal imaging?"

**Very Relevant (4):** "A 65-year-old patient with known renal impairment (eGFR 45 mL/min/1.73m²) requires a contrast-enhanced CT scan of the abdomen. What is the most appropriate approach regarding contrast administration?"

**Highly Relevant (5):** "A 65-year-old patient with known renal impairment (eGFR 45 mL/min/1.73m²) requires a contrast-enhanced CT scan of the abdomen to evaluate for suspected bowel ischemia. The patient has a history of previous contrast reaction. What is the most appropriate approach to imaging in this scenario?"
"""

DIFFICULTY_HELP = """\
## Easy
What is the primary imaging modality used for initial evaluation of suspected acute appendicitis?

## Moderate
A 60-year-old woman with a history of hypertension presents with sudden onset of severe abdominal pain and hypotension. CT of the abdomen shows an abdominal aortic aneurysm with surrounding retroperitoneal fluid. What additional imaging finding would suggest impending rupture of the aneurysm?

## Difficult
A 55-year-old man with a history of cirrhosis presents with worsening abdominal distension and confusion. CT of the abdomen with triple-phase protocol shows a 3 cm hypervascular lesion in segment VII of the liver with washout on portal venous phase. There are also features of portal hypertension. What advanced imaging technique would be most appropriate to further characterize the liver lesion and assist in treatment planning, considering the patient's underlying liver disease?
"""

OPTION_ACCURACY_HELP = """\
- **None:** All provided options are incorrect.
- **All four:** There is no single best answer; all options are correct.
- **Three:** Only one option is incorrect.
- **Two:** Two options could be considered correct answers.
- **One option only:** Ideal scenario for an MCQ.
"""

ASSESSMENT_ACCURACY_HELP = """\
When evaluating the LLM's assessment of each option, you will compare its assessment with your own to determine the number of options the LLM has incorrectly identified.

## Steps to Evaluate

1. **Compare Assessments:** Review each option and compare the LLM's assessment with your own correct or incorrect determinations.
2. **Count Errors:** Count the number of options where the LLM's assessment does not match your own.

### Scenario 1
- **Situation:** You think 1 option is correct and 3 options are incorrect. The LLM has marked one of the incorrect options as correct, and the correct option as incorrect.
- **Your Choice:** "2 incorrect" because the LLM incorrectly assessed 2 options.

### Scenario 2
- **Situation:** The LLM marks 2 options as correct, but one of them is actually incorrect according to your assessment.
- **Your Choice:** "1 incorrect" because the LLM incorrectly assessed 1 option.
"""

FEEDBACK_QUALITY_HELP = """\
### Not Helpful (1)
"The correct answer is B. The other options are incorrect."

### Slightly Helpful (2)
"The correct answer is B) Aortic dissection. The CT angiogram would show a tear in the aortic wall."

### Moderately Helpful (3)
Correct but lacks depth.

### Helpful (4)
Informative with good explanation of correct answer and brief reasoning for incorrect options.

### Very Helpful (5)
Comprehensive, insightful, and educational with imaging findings, clinical correlations, differential diagnosis, and management implications.
"""

COGNITIVE_LEVEL_HELP = """\
**Lower-order cognitive levels:** involve basic recall and understanding of knowledge.

**Higher-order cognitive levels:** involve more complex thinking processes such as:
* Describe Imaging Findings
* Clinical Management
* Apply Concepts
* Calculate and Classify
* Analyze Disease Associations
* Evaluation
"""


# ── Build one question's survey page ────────────────────────────────────────

def build_question_survey(survey: ss.StreamlitSurvey, q_num: int, key_suffix: str):
    """Render the 7-metric survey for a single question."""
    st.info(f"Evaluate the following aspects of Question {q_num}:", icon="📝")

    # a. Clarity
    st.markdown(
        "**a. Clarity:** Evaluate how clear and understandable the question and its options are.",
        help=CLARITY_HELP,
    )
    survey.select_slider(
        f"q{q_num}_clarity",
        options=["", "Very Unclear", "Unclear", "Neutral", "Clear", "Very Clear"],
        label_visibility="collapsed",
        key=f"q{q_num}_clarity_{key_suffix}",
        value=None,
    )

    # b. Clinical Relevance
    st.markdown(
        "**b. Clinical Relevance:** Assess how well the question relates to real-world clinical scenarios.",
        help=RELEVANCE_HELP,
    )
    survey.select_slider(
        f"q{q_num}_clinical_relevance",
        options=["", "Not Relevant", "Slightly Relevant", "Moderately Relevant", "Very Relevant", "Highly Relevant"],
        label_visibility="collapsed",
        key=f"q{q_num}_clinical_relevance_{key_suffix}",
        value=None,
    )

    # c. Difficulty
    st.markdown(
        "**c. Difficulty Level:** Evaluate if the question's difficulty is appropriate for the intended level of the exam.",
        help=DIFFICULTY_HELP,
    )
    survey.select_slider(
        f"q{q_num}_difficulty",
        options=["", "Easy", "Moderate", "Difficult"],
        label_visibility="collapsed",
        key=f"q{q_num}_difficulty_{key_suffix}",
        value=None,
    )

    # d. Option Accuracy
    st.markdown(
        "**d. Option Accuracy:** Based on your assessment, how many options can be considered correct?",
        help=OPTION_ACCURACY_HELP,
    )
    survey.select_slider(
        f"q{q_num}_option_accuracy",
        options=["", "None", "All four", "Three", "Two", "One option only"],
        label_visibility="collapsed",
        key=f"q{q_num}_option_accuracy_{key_suffix}",
        value=None,
    )

    # e. Assessment Accuracy
    st.markdown(
        "**e. Assessment Accuracy:** Evaluate the LLM's assessment of each option compared to your own. How accurate is the LLM's assessment (based on the number of incorrectly interpreted options)?",
        help=ASSESSMENT_ACCURACY_HELP,
    )
    survey.select_slider(
        f"q{q_num}_assessment_accuracy",
        options=["", "All 4 incorrect", "3 incorrect", "2 incorrect", "1 incorrect", "All accurately identified"],
        label_visibility="collapsed",
        key=f"q{q_num}_assessment_accuracy_{key_suffix}",
        value=None,
    )

    # f. Feedback Quality
    st.markdown(
        "**f. Feedback Quality:** Rate how detailed and helpful the feedback provided for the answers is.",
        help=FEEDBACK_QUALITY_HELP,
    )
    survey.select_slider(
        f"q{q_num}_feedback_quality",
        options=["", "Not Helpful", "Slightly Helpful", "Moderately Helpful", "Helpful", "Very Helpful"],
        label_visibility="collapsed",
        key=f"q{q_num}_feedback_quality_{key_suffix}",
        value=None,
    )

    # g. Cognitive Level
    st.markdown(
        "**g. Identify the Primary Cognitive Level:** For each MCQ stem, identify the highest level of cognitive skill required to answer correctly:",
        help=COGNITIVE_LEVEL_HELP,
    )
    survey.selectbox(
        f"q{q_num}_cognitive_level",
        options=["Lower-order cognitive levels", "Higher-order cognitive levels"],
        label_visibility="collapsed",
        index=None,
        key=f"q{q_num}_cognitive_level_{key_suffix}",
    )

    st.success(f"Evaluation of Question {q_num} finishes here", icon="✨")


# ── Main UI ─────────────────────────────────────────────────────────────────

st.title("📋 OSCE Question Review Interface")
st.markdown(
    f"Hello {rater_name}, evaluate the OSCE session below from a random model."
)

# ── Load session to rate ────────────────────────────────────────────────────
# In production, sessions are fetched from MongoDB.
# Here, we load a random session from the pre-recorded db.osce_qa.json.

def load_random_database_session() -> dict | None:
    db_file = "data/db.osce_qa.json"
    if not os.path.exists(db_file):
        return None

    # =========================================================================
    # PRODUCTION MONGODB CONNECTION CODE (COMMENTED)
    # =========================================================================
    # In production, this would look like:
    # 
    # from pymongo import MongoClient
    # 
    # def load_session_from_mongodb(rater_id, db_uri="mongodb://localhost:27017/"):
    #     client = MongoClient(db_uri)
    #     db = client["boards_ai"]
    #     
    #     # 1. Fetch all unique rated (uid, model) sessions for this rater
    #     rated_cursor = db["ratings"].find({"rater": rater_id}, {"uid": 1, "model": 1})
    #     rated_pairs = {(r["uid"], r["model"]) for r in rated_cursor}
    #     
    #     # 2. Fetch all generated sessions from the database
    #     all_sessions = list(db["osce_sessions"].find({}))
    #     
    #     # 3. Filter out the ones that are already rated
    #     unrated = [
    #         s for s in all_sessions
    #         if (s["uid"], s["model"]) not in rated_pairs
    #     ]
    #     
    #     # 4. Return a random choice or None
    #     if unrated:
    #         return random.choice(unrated)
    #     return None
    # =========================================================================

    # Determine which (uid, model) pairs have already been rated by scanning the ratings directory
    rated_sessions = set()
    if os.path.exists(RATINGS_DIR):
        for fname in os.listdir(RATINGS_DIR):
            if fname.endswith(".json"):
                fpath = os.path.join(RATINGS_DIR, fname)
                try:
                    with open(fpath, "r") as f:
                        data = json.load(f)
                        uid = data.get("uid")
                        model = data.get("model")
                        if uid is not None and model is not None:
                            rated_sessions.add((int(uid), normalize_model_name(str(model))))
                except Exception:
                    pass

    try:
        with open(db_file, "r") as f:
            data = json.load(f)
        available_sessions = []
        for doc in data:
            for s in doc.get("session_data", []):
                available_sessions.append(s)

        # Filter out already rated sessions
        unrated_sessions = [
            s for s in available_sessions
            if (int(s.get("uid", 0)), normalize_model_name(str(s.get("model")))) not in rated_sessions
        ]

        if unrated_sessions:
            return random.choice(unrated_sessions)
        elif available_sessions:
            st.session_state.all_rated = True
            return None
    except Exception as e:
        st.error(f"Error reading db.osce_qa.json: {e}")
    return None

if st.session_state.rater_session is None:
    selected_sess = load_random_database_session()
    if selected_sess:
        uid = selected_sess.get("uid")
        case_raw = load_case_by_uid(uid)
        if case_raw:
            fields = extract_case_fields(case_raw)
            collage_b64, _ = process_images(fields["case_images"])
            st.session_state.rater_session = {
                "condition": fields["heading"],
                "chat_history": selected_sess["chat_history"],
                "uid": uid,
                "system": selected_sess.get("system") or fields["system"],
                "image": collage_b64,
                "model": selected_sess.get("model"),
                "citation": fields.get("citation"),
            }
        else:
            st.error(f"Failed to load case data for UID {uid}.")
    else:
        if not st.session_state.get("all_rated", False):
            st.info("No pre-recorded database sessions found. Please make sure data/db.osce_qa.json exists.")


# ── Display session + Survey ────────────────────────────────────────────────

if st.session_state.get("all_rated", False):
    st.success("🎉 **All available OSCE sessions have been rated!**")
    st.info("Thank you for completing the benchmark evaluation. There are no more sessions left to rate.")
else:
    session = st.session_state.rater_session
    if session:
        cols = st.columns(2)

    with cols[0]:
        # Display case image
        if session.get("image"):
            st.image(session["image"])

        # Display chat history
        chat = session.get("chat_history", [])
        question_idx = 1
        for msg in chat:
            if msg["role"] == "assistant":
                with st.chat_message("assistant"):
                    content = msg["content"]
                    if "**Question:**" in content:
                        content = content.replace("**Question:**", f"**Question {question_idx}:**", 1)
                        question_idx += 1
                    st.markdown(content)
            elif msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])

        # Final answer
        if session.get("condition"):
            st.success(f"Final answer: {session['condition']}")
            
        # Citation
        if session.get("citation"):
            st.info(f"**Image Reference:** {session['citation']}")

    with cols[1]:
        with st.expander("Advanced Feedback", expanded=True):
            key_suffix = str(st.session_state.rater_survey_key)
            survey = ss.StreamlitSurvey(f"Survey - Advanced Feedback {key_suffix}")

            def submit_feedback():
                survey_json = survey.to_json()
                data_dict = json.loads(survey_json)

                # Validate all questions answered
                if any(
                    v.get("value") in [None, ""]
                    for v in data_dict.values()
                ):
                    st.warning("Please provide responses for all questions and then submit again.")
                    return

                # Save to local file
                feedback_entry = {
                    "rater": st.session_state.rater_name or "Rater 1",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "uid": session.get("uid"),
                    "system": session.get("system"),
                    "condition": session.get("condition"),
                    "model": session.get("model"),
                    "survey_data": data_dict,
                }

                fname = f"rating_{session.get('uid', 'unknown')}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
                fpath = os.path.join(RATINGS_DIR, fname)
                with open(fpath, "w") as f:
                    json.dump(feedback_entry, f, indent=2)

                st.session_state.last_saved_rating = feedback_entry
                st.session_state.last_saved_filename = fname

            if st.session_state.last_saved_rating:
                st.success(f"Feedback saved to `{st.session_state.last_saved_filename}` ✓")
                json_bytes = json.dumps(st.session_state.last_saved_rating, indent=2).encode('utf-8')
                st.download_button(
                    label="📥 Download Rating JSON",
                    data=json_bytes,
                    file_name=st.session_state.last_saved_filename,
                    mime="application/json"
                )
                st.info("In production, this recorded JSON was programmatically sent to our central MongoDB database for aggregation and statistical analysis.")
                if st.button("Rate Another Session"):
                    st.session_state.last_saved_rating = None
                    st.session_state.last_saved_filename = None
                    st.session_state.rater_survey_key += 1
                    st.session_state.rater_session = None
                    st.session_state.all_rated = False
                    st.rerun()
            else:
                pages = survey.pages(3, on_submit=submit_feedback)
                with pages:
                    if pages.current == 0:
                        build_question_survey(survey, 1, key_suffix)
                    elif pages.current == 1:
                        build_question_survey(survey, 2, key_suffix)
                    elif pages.current == 2:
                        build_question_survey(survey, 3, key_suffix)
