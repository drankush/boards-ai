"""
BOARDS-AI — Welcome Page
==========================
Landing page, API-key configuration, and database architecture documentation.

Run with:
    streamlit run Welcome.py
"""

import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(
    page_title="BOARDS-AI Mock Simulator",
    page_icon="🎓",
    layout="wide",
)

# ── Sidebar: API Key Configuration ──────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    # Try to load from environment first
    env_key = os.getenv("OPENROUTER_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    api_key = st.text_input(
        "OpenRouter API Key (Optional)",
        value=env_key,
        type="password",
        help="Enter your OpenRouter API key for Live Mode. Leave empty to use pre-recorded Mock Mode.",
    )
    if api_key:
        st.session_state["openrouter_api_key"] = api_key
        st.success("OpenRouter API key configured (Live Mode) ✓", icon="🔑")
    else:
        st.info("No API key set. Running in Mock Mode (offline simulation).", icon="ℹ️")

    st.divider()
    st.caption("Built for the BOARDS-AI research project.")

# ── Main Content ────────────────────────────────────────────────────────────
st.title("🎓 BOARDS-AI: Admin Portal & Rater Portal")

st.markdown("""
### Open-Source Mock Implementation

This is a **sanitized, local-first mock implementation** demonstrating the two key applications of the BOARDS-AI platform described in the accompanying manuscript:

1. **Admin Portal** — Ingests radiology cases and runs all four models simultaneously to generate questions, automatically select responses, and evaluate answers.
2. **Rater Portal** — Allows raters to perform human evaluation of the generated sessions.

> [!NOTE]
> In the production environment, the **Admin Portal** and the **Rater Portal** were two separate, decoupled applications. The raters evaluating the generated sessions in the Rater Portal were completely **blinded** to which model generated the OSCE session displayed to them.

---

### 🚀 Getting Started

1. **Run in Mock Mode (No API key needed)**:
   - Navigate directly to **Admin Portal** from the sidebar.
   - Choose **Mondor disease (Mock Case 30244)**.
   - Click the start session button to experience the multi-model generation pipeline with pre-recorded questions, answers, and evaluations.
2. **Run in Live Mode (API key required)**:
   - Enter your **OpenRouter API key** in the sidebar.
   - Add your own case data by placing JSON case files in the `data/` directory (following the schema in `data/case_schema.json`).
   - Run the Admin Portal to execute live LLM generation and evaluation for all four models in parallel.
3. Navigate to the **Rater Portal** to review and evaluate the generated sessions.

---

### 📂 Ingested Case JSON Structure (Cloudinary Data Package)

BOARDS-AI ingested radiology cases structured as JSON files. Below is the architecture of the data package for each case (e.g. Case 30244, Mondor Disease), with value elements truncated for illustration:

```json
{
  "Heading": "Mondor disease - breast",
  "Presentation": "Presentation\\nReferred for diagnostic mammography. She complains of a 3 weeks history of left breast discomfort and feels a ropy linear subcutaneous density...",
  "Patient Data": "Patient Data\\nAge:\\n55 years\\nGender:\\nFemale",
  "Study Findings": [
    {
      "modality": "ultrasound",
      "findings": "US images with color flow of the palpable abnormality in the Lt breast: The study shows a thrombosed subcutaneous vein. Ultrasound features of Mondor disease."
    }
  ],
  "Case Discussion": "Case Discussion\\nIn clinical practice this is an uncommon diagnosis...",
  "Case Related Articles": [
    {
      "title": "Mondor disease (breast)",
      "url": "https://radiopaedia.org/articles/mondor-disease-breast?lang=us",
      "text": "**Mondor disease** is a rare benign **breast** condition characterized by thrombophlebitis of the subcutaneous veins of the breast and anterior chest wall...",
      "systems": "Breast, Urogenital"
    }
  ],
  "Citation": "Case courtesy of Garth Kruger, [Radiopaedia.org](https://radiopaedia.org/). From the case [rID: 18512](https://radiopaedia.org/cases/18512)",
  "Case Images": [
    {
      "base64": "data:image/png;base64,iVBORw0KGgoAAAANS...",
      "caption": "Palpable abnormality ultrasound findings"
    }
  ],
  "uid": 30244
}
```

""")

st.info(
    "👈 Use the sidebar to navigate to the **Admin Portal** or **Rater Portal**.",
    icon="ℹ️",
)
