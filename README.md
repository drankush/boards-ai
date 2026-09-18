<div align="center">

<img src="aiboards_logo.jpeg" alt="BOARDS-AI" width="420">

# BOARDS-AI

**Reference implementation for the LLM-driven radiology OSCE simulator described in _Radiology Advances_.**

[![DOI](https://img.shields.io/badge/DOI-10.1093%2Fradadv%2Fumag039-1a7f37)](https://doi.org/10.1093/radadv/umag039)
[![Journal](https://img.shields.io/badge/Radiology%20Advances-RSNA-002147)](https://academic.oup.com/radadv)
[![Simulator Demo](https://img.shields.io/badge/demo-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://boards-ai.streamlit.app/)
[![Data Explorer](https://img.shields.io/badge/Data%20Explorer-GitHub%20Pages-24292e?logo=github&logoColor=white)](https://drankush.github.io/boards-ai/)

[![Code licence: MIT](https://img.shields.io/badge/code%20licence-MIT-yellow)](LICENSE)
[![Dataset licence: CC BY-NC-SA 3.0](https://img.shields.io/badge/dataset%20licence-CC%20BY--NC--SA%203.0-lightgrey)](data/LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-141210?style=flat-square&logo=openrouter&logoColor=white)](https://openrouter.ai/)
</div>

---

## The paper

> Ankush A, Burman S, Smith S, Gupta V, Barath S, Puranik M, Ponnatapura J.
> **Benchmarking large language model performance in generating and assessing radiology objective structured clinical examination.**
> *Radiology Advances.* 2026:umag039. doi:[10.1093/radadv/umag039](https://doi.org/10.1093/radadv/umag039)

<details>
<summary>BibTeX</summary>

```bibtex
@article{ankush2026benchmarking,
  author  = {Ankush, Ankush and Burman, Samriddhi and Smith, Sydney and
             Gupta, Vivek and Barath, Sitaram and Puranik, Monika and
             Ponnatapura, Janardhana},
  title   = {Benchmarking large language model performance in generating and
             assessing radiology objective structured clinical examination},
  journal = {Radiology Advances},
  year    = {2026},
  pages   = {umag039},
  doi     = {10.1093/radadv/umag039}
}
```

</details>

---

## What this is

BOARDS-AI uses large language models to generate interactive, case-based OSCE
(Objective Structured Clinical Examination) sessions for radiology education. The pipeline:

1. **Ingests** radiology case data — clinical vignette, imaging findings, reference article
2. **Generates** an OSCE-style MCQ with four options by zero-shot, in-context learning
3. **Evaluates** a candidate response and returns structured, educational feedback
4. **Benchmarks** output quality through a blinded expert-rater portal

### Relationship to the published study

This repository is a **local-first reference implementation**, not the production deployment.
The parts that matter scientifically are identical to those used in the study — the prompt
templates in [`prompts.py`](prompts.py), the session logic, the rating instrument, and the
statistical code. Production cloud dependencies have been substituted so the project runs on
a laptop:

| Study deployment | This repository |
|---|---|
| Four provider SDKs (OpenAI, Anthropic, Google, Meta) | Single OpenRouter endpoint, any model |
| MongoDB session store | Local JSON files |
| Cloudinary CDN for case images | Base64 images embedded in the case JSON |
| 50-case Radiopaedia dataset | One attributed demonstration case |

**Reproducibility note.** The study queried GPT-4o, Llama 3-70b, Claude 3.5 Sonnet and
Gemini 1.5 Flash in **August 2024**. Those model versions are retired or altered, so running
this code today will not reproduce the paper's generations verbatim. It reproduces the
*method*, not the outputs.

---

## Interactive Demos & Tools

| Tool | Access | Description |
|---|---|---|
| **OSCE Simulator** | [![Simulator Demo](https://img.shields.io/badge/demo-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://boards-ai.streamlit.app/) [`boards-ai.streamlit.app`](https://boards-ai.streamlit.app/) | Interactive 3-question mock OSCE simulator & blinded rater portal |
| **Data Explorer** | [![Data Explorer](https://img.shields.io/badge/Data%20Explorer-GitHub%20Pages-24292e?logo=github&logoColor=white)](https://drankush.github.io/boards-ai/) [`drankush.github.io/boards-ai`](https://drankush.github.io/boards-ai/) | Web-based side-by-side viewer for LLM questions & evaluations |

### Interactive Data Explorer
The [**BOARDS-AI Data Explorer**](https://drankush.github.io/boards-ai/) provides a browser-based interface to inspect the study dataset:
- **Filter & Search**: Browse radiology cases across 10 subspecialties.
- **Model Comparison**: View and compare model-generated OSCE questions and evaluations side-by-side across all four evaluated LLMs (GPT-4o, Llama 3-70b, Claude 3.5 Sonnet, Gemini 1.5 Flash).
- **Dataset Access**: The generated dataset is distributed under [CC BY-NC-SA 3.0](data/LICENSE). Full dataset access is available for non-commercial academic research upon request.

## Quick start

```bash
# 1. Clone and install
git clone https://github.com/drankush/BOARDS-AI-Code-Sharing
cd BOARDS-AI-Code-Sharing
pip install -r requirements.txt

# 2. Configure your API key
cp .env.example .env
#    Edit .env and add your OpenRouter key, or paste it into the app sidebar at runtime

# 3. Run
streamlit run Welcome.py
```

Developed and reported on **Python 3.11.12** with **Streamlit 1.32.0**.
[`requirements.txt`](requirements.txt) specifies compatible ranges; pin to those two versions
to match the study environment exactly.

---

## Repository structure

```
.
├── index.html                       # Data Explorer web app (GitHub Pages)
├── app.js                           # Explorer client & API integration
├── styles.css                       # Explorer styles (light & dark mode)
├── Welcome.py                       # Streamlit simulator landing page
├── pages/
│   ├── 1_Admin_Portal.py            # Interactive OSCE session engine
│   └── 2_Rater_Portal.py            # Blinded expert benchmarking form
├── prompts.py                       # LLM prompt templates (generation + evaluation)
├── case_loader.py                   # Local JSON case loader
├── image_utils.py                   # Image collage builder
├── data/
│   ├── case_schema.json             # Case data schema documentation
│   ├── 30244.json                   # Demonstration case (Radiopaedia, attributed)
│   ├── db.osce_qa.json              # Pre-recorded rated sessions for the Rater Portal
│   └── LICENSE                      # CC BY-NC-SA 3.0 — applies to this directory
├── Statistical-Analysis/
│   ├── Calculate_GwetAC2.py         # Gwet's AC1/AC2 inter-rater reliability
│   ├── Accuracy_Metrics_Calculation.py  # TBA / 2TBA / AS4A / P5A thresholds
│   └── BOARDS AI sas.sas            # GEE models and Borda ranking (SAS 9.4)
├── .devcontainer/devcontainer.json  # Reproducible dev container
├── .streamlit/config.toml           # Theme
├── requirements.txt
├── .env.example
├── CITATION.cff
└── LICENSE                          # MIT — applies to code
```

---

## Key components

### Prompt templates — [`prompts.py`](prompts.py)

The verbatim prompts used in the study.

- **Question generation** — instructs the model to produce an OSCE-style MCQ with four
  options from the case data. Within a session, previously generated questions are supplied
  to the prompt *solely* to enforce concept non-repetition; questions are not chained, and no
  anchor stem is shared.
- **Evaluation** — produces structured feedback covering correct and incorrect option
  analysis plus an overall performance score.

### Admin Portal — [`pages/1_Admin_Portal.py`](pages/1_Admin_Portal.py)

Loads a random case, renders its images as a tiled collage, then runs the three-question
session: generate MCQ → assign a random option as the candidate response → repeat ×3 →
evaluate all responses with structured feedback.

### Rater Portal — [`pages/2_Rater_Portal.py`](pages/2_Rater_Portal.py)

The blinded benchmarking instrument, scoring each question on:

| Metric | Scale |
|---|---|
| Clarity | 5-point |
| Clinical relevance | 5-point |
| Difficulty | 3-point (Easy / Moderate / Difficult) |
| Option accuracy | 5-point |
| Assessment accuracy | 5-point |
| Feedback quality | 5-point |
| Cognitive level\* | 2-category |

\* Collected in the platform but not analysed in the present study. Difficulty was collected
but excluded from comparative analysis because of poor inter-rater agreement — see the paper.

Ratings are written as JSON to `ratings/` (git-ignored).

### Statistical analysis — [`Statistical-Analysis/`](Statistical-Analysis)

Inter-rater reliability (Gwet's AC2 with quadratic weights), the threshold accuracy
metrics, and the SAS code for the generalized estimating equation models and Borda count ranking reported in the paper.

---

## Adding your own cases

1. Create a `.json` file in `data/`
2. Follow the structure in [`data/case_schema.json`](data/case_schema.json)
3. Required fields: `Heading`, `Presentation`, `Patient Data`, `Study Findings`,
   `Case Related Articles`, `Citation`, `Case Images`, `uid`
4. Images must be base64-encoded with a data-URI prefix, e.g. `data:image/png;base64,...`

---

## Data provenance and licensing

This repository is **dual-licensed**.

| Scope | Licence |
|---|---|
| Source code (`*.py`, `index.html`, `app.js`, `styles.css`, `case_schema.json`) | [MIT](LICENSE) |
| Generated Dataset & Case content (`data/`, Explorer dataset) | [CC BY-NC-SA 3.0](data/LICENSE) |

`data/30244.json` and the session records in `data/db.osce_qa.json` contain material from
Radiopaedia.org, redistributed here under CC BY-NC-SA 3.0 with attribution:

> Case courtesy of Garth Kruger, [Radiopaedia.org](https://radiopaedia.org/) — from the case
> [rID: 18512](https://radiopaedia.org/cases/18512). Reference article: Radswiki T, Elfeky M,
> Weerakkody Y, et al. *Mondor disease (breast)*, Radiopaedia.org (accessed 4 June 2024),
> [doi:10.53347/rID-12346](https://doi.org/10.53347/rID-12346). Licensed under
> [CC BY-NC-SA 3.0](https://radiopaedia.org/licence).

**A single demonstration case is included** so the simulator runs out of the box. The 50-case
study dataset is not redistributed. If you build on the `data/` contents you must attribute
Radiopaedia, keep the use non-commercial, and license your derivative under the same terms.

Material was obtained in June 2024 under the licence terms then in force. Radiopaedia
introduced an application process for non-commercial AI-related use on 6 December 2024;
consult [radiopaedia.org/licence](https://radiopaedia.org/licence) before any new AI-related
use of their content.

---

## Acknowledgements

Case material from [Radiopaedia.org](https://radiopaedia.org/), used under CC BY-NC-SA 3.0.
Model access for the reference implementation is routed through
[OpenRouter](https://openrouter.ai/models).
