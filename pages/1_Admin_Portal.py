"""
BOARDS-AI — OSCE Simulator Page
=================================
Interactive 3-question OSCE session with LLM-generated MCQs and evaluation.
Mirrors the production logic from ``1__Boards_AI.py``, with pre-recorded mock data and OpenRouter.
"""

import streamlit as st
import json
import re
import time
import random
import os
from openrouter import OpenRouter

from case_loader import load_all_cases, extract_case_fields
from image_utils import process_images
from prompts import (
    QUESTION_GENERATION_SYSTEM_PROMPT,
    EVALUATION_SYSTEM_PROMPT,
    build_question_instruction,
    build_evaluation_instruction,
)

st.set_page_config(page_title="Admin Portal", page_icon="🎓", layout="wide")

NUM_QUESTIONS = 3

OPENROUTER_MODEL_MAP = {
    "openai/gpt-4o-2024-08-06": "openai/gpt-4o-2024-08-06",
    "meta-llama/llama-3.0-70b": "meta-llama/llama-3-70b-instruct",
    "google/gemini-1.5-flash": "google/gemini-1.5-flash",
    "anthropic/claude-sonnet-3.5": "anthropic/claude-3-5-sonnet",
}

MODELS = [
    "openai/gpt-4o-2024-08-06",
    "meta-llama/llama-3.0-70b",
    "google/gemini-1.5-flash",
    "anthropic/claude-sonnet-3.5",
]

# ── Helpers ─────────────────────────────────────────────────────────────────

# =============================================================================
# PRODUCTION CLOUDINARY FETCHING MOCK CODE (COMMENTED)
# =============================================================================
# In production, case JSONs are fetched dynamically from Cloudinary.
# For Django/Python configuration details, refer to:
# https://cloudinary.com/documentation/django_integration
#
# import cloudinary
# import cloudinary.api
# import requests
# 
# # Setup Cloudinary configuration from secrets.toml (or fallback to environment variables)
# # CLOUDINARY_URL format: "cloudinary://<api_key>:<api_secret>@<cloud_name>"
# cloudinary_url = st.secrets.get("CLOUDINARY_URL") or os.getenv("CLOUDINARY_URL")
# if cloudinary_url:
#     credentials = cloudinary_url.replace("cloudinary://", "").split("@")
#     api_key, api_secret = credentials[0].split(":")
#     cloud_name = credentials[1]
#     cloudinary.config(
#         cloud_name=cloud_name,
#         api_key=api_key,
#         api_secret=api_secret,
#         secure=True
#     )
# 
# def fetch_specific_json_from_cloudinary(uid: int, folder: str = "files/boardsai") -> dict | None:
#     """Fetches a specific case JSON file from Cloudinary by its UID."""
#     try:
#         public_id = f"{folder}/{uid}.json"
#         # Generate URL to the raw resource on Cloudinary CDN
#         json_url = cloudinary.utils.cloudinary_url(public_id, resource_type="raw")[0]
#         response = requests.get(json_url)
#         if response.status_code == 200:
#             return response.json()
#         else:
#             st.error(f"Failed to fetch JSON from Cloudinary: HTTP {response.status_code}")
#             return None
#     except Exception as e:
#         st.error(f"Cloudinary fetch exception: {e}")
#         return None
# =============================================================================

# =============================================================================
# PRODUCTION MONGODB & GENERATION PIPELINE MOCK CODE (COMMENTED)
# =============================================================================
# In production, when a user clicks "Start OSCE Session":
# 1. Connect to MongoDB to retrieve a list of UIDs that have already been generated.
# 2. Skip those UIDs to avoid duplicates, and select a new UID.
# 3. Fetch the case JSON from Cloudinary, parse it, and initialize the session.
# 4. Once all models have completed their generation, compile and save the combined 
#    data to the "osce_gen_data" MongoDB collection.
#
# from pymongo import MongoClient
#
# def start_session_pipeline():
#     # Read the MongoDB connection URI from secrets.toml (or fallback to localhost)
#     db_uri = st.secrets.get("MONGODB_URI", "mongodb://localhost:27017/")
#     client = MongoClient(db_uri)
#     db = client["boards_ai"]
#
#     # 1. Get already generated case UIDs
#     generated_uids = {doc["uid"] for doc in db["osce_gen_data"].find({}, {"uid": 1})}
#
#     # 2. Pick a new UID that hasn't been generated yet
#     all_available_uids = [30244, 30245, 30246] # Or loaded from a list
#     target_uid = None
#     for uid in all_available_uids:
#         if uid not in generated_uids:
#             target_uid = uid
#             break
#
#     if not target_uid:
#         st.warning("All available cases have already been generated!")
#         return
#
#     # 3. Fetch from Cloudinary
#     case_json = fetch_specific_json_from_cloudinary(target_uid)
#     if case_json:
#         start_case_session(case_json)
#
# def save_session_to_mongodb(combined_json_data):
#     """Sends the finalized generation session data to MongoDB."""
#     db_uri = st.secrets.get("MONGODB_URI", "mongodb://localhost:27017/")
#     client = MongoClient(db_uri)
#     db = client["boards_ai"]
#     db["osce_gen_data"].insert_one(combined_json_data)
# =============================================================================

def get_openrouter_client() -> OpenRouter | None:
    """Return an OpenRouter client using the key from session state, secrets, or environment."""
    try:
        secrets_openrouter = st.secrets.get("openrouter_api_key")
        secrets_openai = st.secrets.get("openai_api_key")
    except Exception:
        secrets_openrouter = None
        secrets_openai = None

    api_key = (
        st.session_state.get("openrouter_api_key")
        or st.session_state.get("openai_api_key")
        or secrets_openrouter
        or secrets_openai
        or os.environ.get("OPENROUTER_API_KEY")
    )
    if not api_key:
        return None
    return OpenRouter(
        api_key=api_key,
        http_referer="https://github.com/drankush/BOARDS-AI",
        x_open_router_title="BOARDS-AI Admin Portal",
    )


def extract_with_regex(text: str) -> dict:
    """Fallback regex parser for malformed JSON responses."""
    text = text.replace('"', "'")
    question_pattern = r"'stem'\s*:\s*'((?:[^'\\\\]|\\\\.)*)'"
    question_match = re.search(question_pattern, text, re.DOTALL)
    question = question_match.group(1) if question_match else "Question not found"

    options_pattern = r"'options'\s*:\s*\[(.*?)\]"
    options_match = re.search(options_pattern, text, re.DOTALL)
    options_text = options_match.group(1) if options_match else ""

    option_detail = r"\{\s*'id'\s*:\s*'([^']+)'\s*,\s*'text'\s*:\s*'((?:[^'\\\\]|\\\\.)*?)'\s*\}"
    options = re.findall(option_detail, options_text)

    return {
        "question": {
            "stem": question,
            "options": [{"id": o[0], "text": o[1]} for o in options],
        }
    }


def format_as_markdown(data: dict) -> str:
    """Format parsed question JSON as Markdown for display."""
    q = data["question"]
    md = f"**Question:**\n{q['stem']}\n\n**Options:**"
    for opt in q["options"]:
        md += f"\n\n\n{opt['id']}. {opt['text']}"
    return md


def llm_request_question(model: str, instruction: str, max_retries: int = 3) -> str:
    """Send a question-generation request to the LLM."""
    client = get_openrouter_client()
    if client is None:
        return "⚠️ No API key configured. Please set it in the sidebar."

    # Map user-friendly model name to OpenRouter model ID
    model_id = OPENROUTER_MODEL_MAP.get(model, model)

    # Determine sampling parameters
    temperature = 1.0
    top_p = 0.95 if "gemini" in model.lower() or "gemini" in model_id.lower() else 1.0
    max_tokens = 4096

    for attempt in range(max_retries):
        try:
            with client:
                response = client.chat.send(
                    model=model_id,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": QUESTION_GENERATION_SYSTEM_PROMPT},
                        {"role": "user", "content": instruction},
                    ],
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    timeout_ms=30000,
                )
            content = response.choices[0].message.content
            if content:
                try:
                    data = json.loads(content)
                    return format_as_markdown(data)
                except json.JSONDecodeError:
                    data = extract_with_regex(content)
                    return format_as_markdown(data)
        except Exception as e:
            st.warning(f"LLM attempt {attempt + 1} failed for {model}: {e}")
            time.sleep(1)

    return f"❌ Failed to generate question via {model} after multiple attempts."


def llm_request_evaluation(model: str, instruction: str, max_retries: int = 3) -> str:
    """Send an evaluation request to the LLM."""
    client = get_openrouter_client()
    if client is None:
        return "⚠️ No API key configured."

    # Map user-friendly model name to OpenRouter model ID
    model_id = OPENROUTER_MODEL_MAP.get(model, model)

    # Determine sampling parameters
    temperature = 1.0
    top_p = 0.95 if "gemini" in model.lower() or "gemini" in model_id.lower() else 1.0
    max_tokens = 4096

    for attempt in range(max_retries):
        try:
            with client:
                response = client.chat.send(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": EVALUATION_SYSTEM_PROMPT},
                        {"role": "user", "content": instruction},
                    ],
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    timeout_ms=60000,
                )
            if response.choices:
                return response.choices[0].message.content
        except Exception as e:
            st.warning(f"Evaluation attempt {attempt + 1} failed for {model}: {e}")
            time.sleep(1)

    return f"❌ Failed to evaluate via {model} after multiple attempts."


def load_mock_session(model_name: str, uid: int) -> dict | None:
    """Load pre-recorded session data for a specific model and case UID."""
    try:
        model_mapping = {
            "openai/gpt-4o-2024-08-06": "gpt-4o",
            "meta-llama/llama-3.0-70b": "llama3-70b-8192",
            "anthropic/claude-sonnet-3.5": "anthropic/claude-3.5-sonnet",
            "google/gemini-1.5-flash": "gemini-1.5-flash-latest"
        }
        target_model = model_mapping.get(model_name)
        if not target_model:
            return None

        mock_file = "data/db.osce_qa.json"
        if os.path.exists(mock_file):
            with open(mock_file, "r") as f:
                data = json.load(f)
                for item in data:
                    for s in item.get("session_data", []):
                        if s.get("uid") == uid and s.get("model") == target_model:
                            return s
    except Exception as e:
        st.error(f"Error loading mock session: {e}")
    return None


# ── Session State Initialization ────────────────────────────────────────────

defaults = {
    "show_question_area": False,
    "show_reset_button": False,
    "condition": None,
    "case_data_text": None,
    "image": None,
    "image_captions": None,
    "reference_article": None,
    "citation": None,
    "article_citation": None,
    "uid": None,
    "system": None,
    "run_as_mock": False,
    "auto_simulation": True,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

for model in MODELS:
    if f"chat_history_{model}" not in st.session_state:
        st.session_state[f"chat_history_{model}"] = []
    if f"current_question_{model}" not in st.session_state:
        st.session_state[f"current_question_{model}"] = 0
    if f"user_answers_{model}" not in st.session_state:
        st.session_state[f"user_answers_{model}"] = []
    if f"input_disabled_{model}" not in st.session_state:
        st.session_state[f"input_disabled_{model}"] = False


# ── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Simulator Settings")

    try:
        secrets_openrouter = st.secrets.get("openrouter_api_key")
        secrets_openai = st.secrets.get("openai_api_key")
    except Exception:
        secrets_openrouter = None
        secrets_openai = None

    has_api_key = (
        bool(st.session_state.get("openrouter_api_key")) 
        or bool(st.session_state.get("openai_api_key"))
        or bool(secrets_openrouter)
        or bool(secrets_openai)
        or bool(os.environ.get("OPENROUTER_API_KEY"))
    )

    if not has_api_key:
        api_key = st.text_input("OpenRouter API Key (Optional)", type="password", help="Needed only for Live Mode.")
        if api_key:
            st.session_state["openrouter_api_key"] = api_key
            st.rerun()
    else:
        st.success("🗝️ API Key Loaded")

    # Load all cases
    cases = load_all_cases()
    st.metric("Available Cases", len(cases))

    # Case Selection
    case_options = []
    case_by_label = {}
    for case in cases:
        uid = case.get("uid", 0)
        heading = case.get("Heading", "Unknown")
        label = f"{heading} (UID {uid})"
        if uid == 30244:
            label = f"★ Mondor Disease (Mock Case {uid})"
        case_options.append(label)
        case_by_label[label] = case

    selected_case_label = st.selectbox(
        "Select Case",
        case_options,
        index=0,
        help="Select the case to simulate. Case 30244 supports offline Mock Mode."
    )
    selected_case = case_by_label.get(selected_case_label)

    # Mode Status Indicator
    is_mock_uid = selected_case.get("uid") == 30244 if selected_case else False
    if is_mock_uid:
        if has_api_key:
            run_as_mock = st.checkbox(
                "Use Mock Data",
                value=True,
                help="Check to simulate using exact questions/evaluations from the paper."
            )
        else:
            run_as_mock = True
            st.info("💡 Running in Mock Mode (offline simulation for case 30244).")
    else:
        run_as_mock = False
        if not has_api_key:
            st.warning("⚠️ Live Mode requires an OpenRouter/OpenAI API key. Enter key or select Mock Case 30244.")

    st.session_state["run_as_mock"] = run_as_mock
    st.session_state["auto_simulation"] = True

    if st.session_state.show_question_area:
        min_q = min(st.session_state[f"current_question_{m}"] for m in MODELS)
        st.metric(
            "Question Progress",
            f"{min(min_q + 1, NUM_QUESTIONS)}/{NUM_QUESTIONS}",
        )


# ── Main UI ─────────────────────────────────────────────────────────────────

st.title("🩻 Admin Portal")
st.caption("Interactive 3-question OSCE session generator with LLM-generated MCQs")


def start_case_session(case_raw: dict):
    """Start an OSCE session for the specified case across all 4 models."""
    fields = extract_case_fields(case_raw)

    # Process images into collage
    collage_b64, _ = process_images(fields["case_images"])

    # Store in session state
    st.session_state.condition = fields["heading"]
    st.session_state.case_data_text = fields["case_data_text"]
    st.session_state.image = collage_b64
    st.session_state.image_captions = fields["image_captions"]
    st.session_state.reference_article = fields["reference_article"]
    st.session_state.citation = fields["citation"]
    st.session_state.article_citation = fields.get("article_citation")
    st.session_state.uid = fields["uid"]
    st.session_state.system = fields["system"]

    # Reset session for all models
    st.session_state.show_question_area = True
    st.session_state.show_reset_button = False

    for model in MODELS:
        st.session_state[f"chat_history_{model}"] = []
        st.session_state[f"current_question_{model}"] = 0
        st.session_state[f"user_answers_{model}"] = []
        st.session_state[f"input_disabled_{model}"] = False

    # Generate first question for each model
    for model in MODELS:
        ask_next_question(model)


def ask_next_question(model: str):
    """Generate the next OSCE question using the LLM or retrieve from mock data for a specific model."""
    curr_q = st.session_state[f"current_question_{model}"]
    if curr_q < NUM_QUESTIONS:
        if st.session_state.run_as_mock:
            # Retrieve from pre-recorded json
            mock_sess = load_mock_session(model, st.session_state.uid)
            if mock_sess:
                chat_history = mock_sess.get("chat_history", [])
                q_idx = curr_q * 2
                if q_idx < len(chat_history):
                    question_md = chat_history[q_idx]["content"]
                    st.session_state[f"chat_history_{model}"].append(
                        {"role": "assistant", "content": question_md}
                    )
                    return
                else:
                    st.error(f"Mock question not found in chat history for {model}.")
            else:
                st.error(f"Mock session data not found for {model}.")
            return

        # Live Mode
        history = st.session_state[f"chat_history_{model}"]
        answers = st.session_state[f"user_answers_{model}"]
        qa_pairs = list(zip(history[::2], answers))
        prev_qa = "\n".join(
            f"Q{i+1}: {q['content']}\nA{i+1}: {a}" for i, (q, a) in enumerate(qa_pairs)
        )

        instruction = build_question_instruction(
            condition=st.session_state.condition,
            case_data=st.session_state.case_data_text,
            image_captions=st.session_state.image_captions,
            reference_article=st.session_state.reference_article,
            previous_qa=prev_qa,
        )

        with st.spinner(f"Generating question live via {model}..."):
            question_md = llm_request_question(model, instruction)

        if "❌" in question_md:
            st.session_state[f"chat_history_{model}"].append(
                {"role": "assistant", "content": question_md}
            )
            st.session_state[f"input_disabled_{model}"] = True
            return

        st.session_state[f"chat_history_{model}"].append(
            {"role": "assistant", "content": question_md}
        )


def evaluate_answers(model: str):
    """Evaluate candidate responses for a specific model."""
    if st.session_state.run_as_mock:
        mock_sess = load_mock_session(model, st.session_state.uid)
        if mock_sess:
            chat_history = mock_sess.get("chat_history", [])
            if len(chat_history) >= 7:
                feedback = chat_history[6]["content"]
                
                # Check answers
                mock_answers = [
                    chat_history[1]["content"],
                    chat_history[3]["content"],
                    chat_history[5]["content"],
                ]
                user_answers = st.session_state[f"user_answers_{model}"]
                
                cleaned_user = [ans[0].upper() if ans else "" for ans in user_answers]
                cleaned_mock = [ans[0].upper() if ans else "" for ans in mock_answers]
                
                if cleaned_user != cleaned_mock:
                    warning_msg = (
                        f"⚠️ **Note on Mock Evaluation:** Random option selected {cleaned_user} "
                        f"instead of the paper's recorded responses {cleaned_mock}. Since you are running in Mock "
                        f"Mode without an API key, we are displaying the pre-recorded evaluation from the paper. "
                        f"To get a dynamic live evaluation of your specific answers, please enter an OpenRouter "
                        f"API key in the sidebar."
                    )
                    st.session_state[f"chat_history_{model}"].append({"role": "assistant", "content": warning_msg})
                
                st.session_state[f"chat_history_{model}"].append({"role": "assistant", "content": feedback})
                st.session_state[f"input_disabled_{model}"] = True
                return
            else:
                st.error(f"Mock evaluation not found for {model}.")
        else:
            st.error(f"Mock session data not found for {model}.")
        return

    # Live Mode
    instruction = build_evaluation_instruction(
        condition=st.session_state.condition,
        case_data=st.session_state.case_data_text,
        image_captions=st.session_state.image_captions,
        reference_article=st.session_state.reference_article,
        chat_history=st.session_state[f"chat_history_{model}"],
        num_questions=NUM_QUESTIONS,
    )

    with st.spinner(f"Evaluating responses live for {model}..."):
        feedback = llm_request_evaluation(model, instruction)

    st.session_state[f"chat_history_{model}"].append({"role": "assistant", "content": feedback})
    st.session_state[f"input_disabled_{model}"] = True


# ── Buttons ─────────────────────────────────────────────────────────────────

if st.button("🚀 Start OSCE Session", type="primary"):
    if not selected_case:
        st.error("Please select a case first.")
    elif not is_mock_uid and not has_api_key:
        st.error("Live Mode requires an OpenAI/OpenRouter API key. Enter key or select Mock Case 30244.")
    else:
        start_case_session(selected_case)
        st.rerun()




# ── Display ─────────────────────────────────────────────────────────────────

if st.session_state.show_question_area:
    # Show case image
    if st.session_state.image:
        st.image(st.session_state.image)

    # Display 4 columns side by side
    cols = st.columns(len(MODELS))
    for idx, model in enumerate(MODELS):
        with cols[idx]:
            # Display model name and provider
            model_short = model.split("/")[-1]
            provider_short = model.split("/")[0]
            st.markdown(f"### {model_short}")
            st.markdown(f"**Provider:** `{provider_short}`")
            st.divider()

            # Display chat history for this model
            for msg in st.session_state[f"chat_history_{model}"]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            # Answer input (Automated simulation mode)
            if not st.session_state[f"input_disabled_{model}"]:
                st.info("🤖 **Random option selection in progress...** Selecting answer automatically in 2 seconds.")

            # Show final answer and citation after evaluation
            if st.session_state[f"input_disabled_{model}"]:
                st.divider()
                st.success(f"**Final Answer:** {st.session_state.condition}")

    # Show citation, download, and reset buttons at the very bottom
    if st.session_state.show_reset_button:
        st.divider()
        if st.session_state.citation:
            st.info(f"**Image Reference:** {st.session_state.citation}")
            
        if st.session_state.article_citation:
            st.info(f"**Article Reference:**\n{st.session_state.article_citation}")

        # Download & Reset layout
        col_down, col_reset = st.columns([1, 1])
        with col_down:
            model_mapping = {
                "openai/gpt-4o-2024-08-06": "gpt-4o",
                "meta-llama/llama-3.0-70b": "llama3-70b-8192",
                "anthropic/claude-sonnet-3.5": "anthropic/claude-3.5-sonnet",
                "google/gemini-1.5-flash": "gemini-1.5-flash-latest"
            }
            session_data_list = []
            for m in MODELS:
                session_entry = {
                    "uid": st.session_state.uid,
                    "reference_article": st.session_state.reference_article,
                    "system": st.session_state.system,
                    "chat_history": st.session_state[f"chat_history_{m}"],
                    "model": model_mapping.get(m, m)
                }
                session_data_list.append(session_entry)
            combined_json = [{
                "session_data": session_data_list
            }]
            json_bytes = json.dumps(combined_json, indent=2).encode('utf-8')
            st.download_button(
                label="📥 Download Combined JSON",
                data=json_bytes,
                file_name=f"combined_session_{st.session_state.uid}.json",
                mime="application/json",
                use_container_width=True
            )
        with col_reset:
            if st.button("🗑️ Reset Session", use_container_width=True):
                for k in defaults:
                    st.session_state[k] = defaults[k]
                for m in MODELS:
                    st.session_state[f"chat_history_{m}"] = []
                    st.session_state[f"current_question_{m}"] = 0
                    st.session_state[f"user_answers_{m}"] = []
                    st.session_state[f"input_disabled_{m}"] = False
                st.rerun()

        st.info("In production, this generated OSCE Session data was programmatically sent to our central MongoDB database for random display to raters at Rater Portal.")



# ── Auto-Simulation Execution ────────────────────────────────────────────────

any_active = any(
    st.session_state.show_question_area
    and not st.session_state[f"input_disabled_{model}"]
    and st.session_state.get("auto_simulation", False)
    for model in MODELS
)

if any_active:
    # Check if all active models have generated their latest question
    ready_to_act = True
    for model in MODELS:
        if not st.session_state[f"input_disabled_{model}"]:
            history = st.session_state[f"chat_history_{model}"]
            if not history or history[-1]["role"] != "assistant":
                ready_to_act = False
                break

    if ready_to_act:
        with st.spinner("🤖 Random option selection in progress..."):
            time.sleep(2)

        # For each active model, select a random option and advance
        for model in MODELS:
            if not st.session_state[f"input_disabled_{model}"]:
                selected_option = random.choice(["A", "B", "C", "D"])
                st.session_state[f"chat_history_{model}"].append(
                    {"role": "user", "content": selected_option}
                )
                st.session_state[f"user_answers_{model}"].append(selected_option)

                curr_q = st.session_state[f"current_question_{model}"]
                if curr_q < NUM_QUESTIONS - 1:
                    st.session_state[f"current_question_{model}"] += 1
                    ask_next_question(model)
                else:
                    evaluate_answers(model)

        # Update show_reset_button if all are done
        all_done = all(st.session_state[f"input_disabled_{model}"] for model in MODELS)
        if all_done:
            st.session_state.show_reset_button = True

        st.rerun()
