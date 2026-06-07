# BOARDS-AI: Mock Simulator

**Sanitized, local-first mock implementation** of the BOARDS-AI Radiology OSCE Simulator platform.

This repository demonstrates the complete pipeline for LLM-driven radiology board examination simulation as described in:

> *[Manuscript title and citation to be added upon publication]*

## Overview

BOARDS-AI uses large language models (LLMs) to generate interactive, case-based OSCE (Objective Structured Clinical Examination) sessions for radiology education. The platform:

1. **Ingests** radiology case data (clinical vignettes, imaging findings, reference articles)
2. **Generates** progressively difficult MCQ questions using zero-shot, in-context learning
3. **Evaluates** candidate responses with structured, educational feedback
4. **Benchmarks** quality through an expert rater survey portal

This mock implementation replaces production cloud dependencies (Cloudinary CDN, MongoDB, multi-provider LLM pool) with local alternatives suitable for reproduction and extension.

## Quick Start

```bash
# 1. Clone and install dependencies
git clone https://github.com/drankush/BOARDS-AI-Code-Sharing
cd boards-ai-simulator
pip install -r requirements.txt

# 2. Configure your API key
cp .env.example .env
# Edit .env and add your OpenRouter API key

# 3. Run the simulator
streamlit run Welcome.py
```

## Repository Structure

```
boards-ai-simulator/
├── Welcome.py                    # Landing page with project overview
├── pages/
│   ├── 1_OSCE_Session_Generator.py # Interactive OSCE session engine
│   └── 2_Rater_Portal.py         # Expert benchmarking survey form
├── prompts.py                    # LLM prompt templates (generation + evaluation)
├── case_loader.py                # Local JSON case loader
├── image_utils.py                # Image collage builder
├── data/
│   ├── case_schema.json          # Case data schema documentation
│   └── demo_case.json            # Synthetic demo case for testing
├── requirements.txt              # Python dependencies
├── .env.example                  # API key template
└── .streamlit/
    └── config.toml               # Streamlit theme configuration
```

## Adding Your Own Cases

1. Create a JSON file in the `data/` directory
2. Follow the schema documented in `data/case_schema.json`
3. Required fields: `Heading`, `Presentation`, `Patient Data`, `Study Findings`, `Case Related Articles`, `Citation`, `Case Images`, `uid`
4. Images must be base64-encoded with a data-URI prefix (e.g., `data:image/jpg;base64,...`)

## Key Components

### Prompt Templates (`prompts.py`)

Contains the **exact LLM prompts** used in the study:

- **Question Generation**: System prompt instructing the LLM to create OSCE-style MCQs with progressive difficulty, using case data for zero-shot in-context learning
- **Evaluation**: System prompt for structured feedback generation covering correct/incorrect option analysis and an overall performance score

### OSCE Session Generator (`pages/1_OSCE_Session_Generator.py`)

Interactive 3-question session:
1. Load a random case from `data/`
2. Display case images as a tiled collage
3. LLM generates MCQ → random option selection → repeat 3×
4. LLM evaluates all responses with structured feedback

### Rater Portal (`pages/2_Rater_Portal.py`)

Expert benchmarking form with 7 metrics per question:
- **Clarity** (5-point scale)
- **Clinical Relevance** (5-point scale)
- **Difficulty Level** (3-point scale)
- **Option Accuracy** (5-point scale)
- **Assessment Accuracy** (5-point scale)
- **Feedback Quality** (5-point scale)
- **Cognitive Level** (2-category)*

*Not part of the current study.

Ratings are saved as JSON files in the `ratings/` directory.


## Dependencies

- Python 3.10+
- [Streamlit](https://streamlit.io/) ≥1.30
- [OpenRouter Python SDK](https://github.com/OpenRouterTeam/python-sdk) ≥0.9.0
- [streamlit-survey](https://github.com/okld/streamlit-survey) 0.1.0
- [streamlit-feedback](https://github.com/trubrics/streamlit-feedback) ≥0.1.3
- [streamlit-option-menu](https://github.com/victoryhb/streamlit-option-menu) ≥0.3.13
- [Pillow](https://python-pillow.org/) ≥10.0

## License

*[License to be specified by authors]*
