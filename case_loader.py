"""
BOARDS-AI — Local Case Loader
==============================
Replaces the production Cloudinary-based case fetching with local JSON files.
Users place their own case JSON files in the ``data/`` directory.
"""

import json
import os
import random


def load_all_cases(data_dir: str = "data") -> list[dict]:
    """Load all JSON case files from the data directory."""
    cases = []
    if not os.path.isdir(data_dir):
        return cases
    for fname in sorted(os.listdir(data_dir)):
        if fname.endswith(".json") and fname not in ("case_schema.json", "database3.osce_qa.json"):
            fpath = os.path.join(data_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if isinstance(data, dict):
                        cases.append(data)
                except json.JSONDecodeError:
                    continue
    return cases


def load_random_case(data_dir: str = "data") -> dict | None:
    """Load a random case from the data directory."""
    cases = load_all_cases(data_dir)
    if not cases:
        return None
    return random.choice(cases)


def load_case_by_uid(uid: int, data_dir: str = "data") -> dict | None:
    """Load a specific case by its UID."""
    cases = load_all_cases(data_dir)
    for case in cases:
        if case.get("uid") == uid:
            return case
    return None


def extract_case_fields(case_data: dict) -> dict:
    """
    Extract and structure the relevant fields from a raw case JSON.

    Returns a dict with:
        - heading (str): The diagnosis / true answer
        - presentation (str): Clinical vignette
        - patient_data (str): Demographics
        - case_data_text (str): Combined presentation + patient data + findings
        - study_findings (list): Raw study findings list
        - reference_article (str): Up to ~750 words from related articles
        - system (str): Subspecialty tag
        - citation (str): Radiopaedia attribution
        - case_images (list): Raw image dicts with base64 + caption
        - image_captions (str): Concatenated caption string
        - uid (int): Case identifier
    """
    heading = case_data.get("Heading", "Unknown")
    presentation = case_data.get("Presentation", "")
    patient_data = case_data.get("Patient Data", "")

    # Study findings
    study_findings = case_data.get("Study Findings", [])
    findings_text = "\n\n".join(
        f"{f['modality']}: {f['findings']}" for f in study_findings
    )
    case_text = f"{presentation}\n\n{patient_data}\n\nStudy Findings:\n{findings_text}"

    # Articles → reference text (up to ~750 words)
    articles = case_data.get("Case Related Articles", [])
    all_words: list[str] = []
    word_count_by_article: list[tuple[int, dict]] = []
    if articles:
        random.shuffle(articles)
        for article in articles:
            article_text = article.get("text", "")
            word_list = article_text.split()
            all_words.extend(word_list)
            word_count_by_article.append((len(word_list), article))
            if len(all_words) >= 750:
                break
        if len(all_words) > 750:
            start = random.randint(0, len(all_words) - 750)
            selected_words = all_words[start : start + 750]
        else:
            selected_words = all_words
        reference_article = " ".join(selected_words)

        # Extracted systems (without references)
        major = max(word_count_by_article, key=lambda x: x[0])[1]
        systems = major.get("systems", "").split(", ")
        system = random.choice(systems) if systems else "General"
    else:
        reference_article = "No reference article available."
        system = "General"

    # Images and captions
    case_images = case_data.get("Case Images", [])
    image_captions = ". ".join(
        f"The image {i + 1} shows {img['caption']}"
        for i, img in enumerate(case_images[:9])
    )

    citation = case_data.get("Citation", "No citation available")
    uid = case_data.get("uid", 0)

    return {
        "heading": heading,
        "presentation": presentation,
        "patient_data": patient_data,
        "case_data_text": case_text,
        "study_findings": study_findings,
        "reference_article": reference_article,
        "system": system,
        "citation": citation,
        "case_images": case_images,
        "image_captions": image_captions,
        "uid": uid,
    }
