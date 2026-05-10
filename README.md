# 🤖 AI HR Shortlisting Agent

> AI-Powered Resume Screening & Candidate Ranking Dashboard

An AI agent prototype that assists HR teams in evaluating candidates efficiently. The agent ingests a Job Description (JD) along with resumes (PDF/DOCX) and/or LinkedIn profile data, then produces a ranked shortlist with a transparent scoring rubric explaining every score.

---

## 📊 Project Presentation

Download the complete project presentation here:
[📥 AI HR Shortlisting Agent PPT](docs/AI_HR_Shortlisting_Agent.pptx)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Agent Architecture](#agent-architecture)
- [Tech Stack & Decision Log](#tech-stack--decision-log)
- [LLM Choice Rationale](#llm-choice-rationale)
- [Prompt Design](#prompt-design)
- [Security Mitigations](#security-mitigations)
- [Installation](#installation)
- [Usage](#usage)
- [Scoring Rubric](#scoring-rubric)
- [Sample Output](#sample-output)
- [Project Structure](#project-structure)

---

## Overview

HR teams routinely screen hundreds of applications per role, leading to fatigue, inconsistency, and unconscious bias. This AI agent standardises evaluation, highlights skill gaps, and surfaces the best-fit candidates faster — while keeping a human in the loop for final decisions.

---

## Features

| Feature | Description |
|---|---|
| JD Parser | Extracts skills, experience, qualifications from Job Description |
| Resume Ingestion | Accepts PDF, DOCX, TXT resumes |
| LinkedIn Ingestion | Accepts JSON, PDF, TXT LinkedIn exports |
| Semantic Matching | Compares candidate profiles to JD using SentenceTransformers embeddings |
| 5-Dimension Scoring | Skills Match, Experience, Projects, Education, Communication |
| ATS Score | Weighted percentage score with gauge chart visualisation |
| Ranked Shortlist | Candidates sorted by total score descending |
| Shortlist Report | Downloadable JSON, TXT, HTML reports with full rubric breakdown |
| Human-in-the-Loop | Recruiter can Shortlist / Hold / Reject with notes — logged to report |

---

## Agent Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    HR AGENT PIPELINE                    │
└─────────────────────────────────────────────────────────┘

Step 1 — INPUT
    HR uploads JD + Resume files / LinkedIn files
            │
            ▼
Step 2 — JD PARSE
    JDParser extracts: title, required skills,
    experience range, domain, qualifications
            │
            ▼
Step 3 — PROFILE PARSE
    ResumeParser / LinkedInParser converts each
    file into structured CandidateProfile fields:
    full_name, skills, experience, education,
    projects_text, headline, source_file
            │
            ▼
Step 4 — DEDUPLICATE
    Remove exact duplicates by (full_name + source_file)
    to handle multiple submissions
            │
            ▼
Step 5 — AI SCORE
    Scorer computes 5-dimension rubric per candidate:
    ┌─────────────────┬────────┬──────────────────────────┐
    │ Skills Match    │  30%   │ Keyword + category match  │
    │ Experience      │  25%   │ Years vs JD requirement   │
    │ Projects        │  20%   │ Semantic similarity + AI  │
    │                 │        │ keyword signals           │
    │ Education       │  15%   │ Degree + domain match     │
    │ Communication   │  10%   │ Resume structure quality  │
    └─────────────────┴────────┴──────────────────────────┘
    SemanticMatcher (SentenceTransformers) adds
    embedding similarity bonus to Projects score
            │
            ▼
Step 6 — RANK
    Ranker sorts candidates by total_score descending
            │
            ▼
Step 7 — REPORT
    ReportGenerator produces JSON + TXT + HTML
    shortlist report with full rubric breakdown
            │
            ▼
Step 8 — HUMAN OVERRIDE
    Recruiter reviews in Streamlit dashboard:
    - Shortlist / Hold / Reject decision
    - Recruiter notes
    - Override logged to report
```

---

## Tech Stack & Decision Log

| Layer | Tool Used | Version | Reason |
|---|---|---|---|
| LLM | Qwen2.5 via Ollama | 1.5b | See rationale below |
| Agent Framework | Custom pipeline (ResumeParser → Scorer → Ranker) | — | Lightweight, no external agent overhead |
| Embeddings | SentenceTransformers `all-MiniLM-L6-v2` | latest | Fast, local, no API cost |
| Resume Parse | PyMuPDF (fitz) + python-docx | latest | Reliable PDF/DOCX extraction |
| LinkedIn Parse | Custom JSON/PDF/TXT parser | — | Handles exported LinkedIn data |
| UI | Streamlit | latest | Rapid prototyping, built-in file upload |
| Visualisation | Plotly | latest | Interactive gauge charts |
| Output | JSON + TXT + HTML | — | Three formats as required |

---

## LLM Choice Rationale

**Model chosen: Qwen2.5:1.5b (local via Ollama)**

| Criterion | Qwen2.5:1.5b (chosen) | GPT-4o | Claude 3.5 Sonnet |
|---|---|---|---|
| Cost | Free (local) | ~$5–15/1M tokens | ~$3–15/1M tokens |
| Privacy | 100% local — no PII sent to cloud | PII sent to OpenAI | PII sent to Anthropic |
| Context Window | 32K tokens | 128K tokens | 200K tokens |
| Setup | Ollama (one command) | API key required | API key required |
| Speed | Fast on CPU | Fast (API) | Fast (API) |
| Offline | ✅ Yes | ❌ No | ❌ No |

**Why Qwen2.5:1.5b over GPT-4o / Claude:**

- Resume data contains **PII (personal identifiable information)**. Running locally ensures candidate data never leaves the machine — critical for HR compliance and GDPR considerations.
- Zero API cost enables unlimited testing with sample resumes during development.
- For a prototype/internship submission, local inference is sufficient for structured scoring tasks.
- The scoring logic is deterministic (keyword matching + weighted calculation), so a smaller LLM handles the reasoning tasks adequately.

> **Trade-off acknowledged:** A larger model (GPT-4o, Claude 3.5) would produce richer natural language justifications and better semantic understanding. In production, a cloud LLM with PII masking would be recommended.

---

## Prompt Design

### JD Parsing Prompt

The JD parser uses a structured extraction prompt that instructs the model to return JSON with defined fields (`title`, `required_skills`, `min_experience_years`, `domain`). This prevents hallucination by constraining the output schema.

**Guardrails applied:**
- Output forced to JSON schema — invalid responses are caught and defaulted
- No free-form generation — only extraction from provided text
- Input length capped to prevent prompt injection via oversized JD files

### Scoring Reasoning Prompt

The reasoning generator uses candidate profile fields + JD requirements to produce a one-paragraph summary. Fields are injected as structured variables, not raw user text, to prevent prompt injection.

**Guardrails applied:**
- Candidate text is sanitised before injection (special characters stripped)
- Scoring is deterministic (not LLM-generated) — LLM only writes the summary text
- Human-in-the-loop review required before any hire decision is acted upon

---

## Security Mitigations

> ⚠️ This section is mandatory per submission guidelines.

| Risk | Description | Mitigation Applied |
|---|---|---|
| **Prompt Injection** | Malicious resume content manipulating agent behaviour | Candidate text sanitised before prompt injection; structured output schema enforced; LLM output parsed with validation |
| **Data Privacy / PII** | Resume and LinkedIn data contains personal information | 100% local processing via Ollama — no candidate PII is sent to any cloud LLM or external API |
| **API Key Exposure** | LLM/API keys leaked in code | No hardcoded keys; `.env` + `python-dotenv` pattern used; `.env` added to `.gitignore`; `.env.example` provided |
| **Hallucination Risk** | LLM generating false scores or wrong recommendations | Scoring is fully deterministic (keyword match + weighted formula); LLM only generates summary text, not scores; human recruiter reviews all decisions |
| **Unauthorised Access** | Anyone triggering the agent endpoint | Application runs locally only; no exposed public endpoint; no authentication needed for local prototype |
| **Data Retention** | Uploaded resumes stored on disk | Temp files cleared at the start of every pipeline run; reports stored locally only |

---

## Installation

### 1. Clone Repository

```bash
git clone <your-github-repo-link>
cd AI-HR-Shortlisting-Agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Ollama

Download from: https://ollama.com/download

### 4. Pull AI Model

```bash
ollama pull qwen2.5:1.5b
```

---

## Usage

### Step 1 — Start Ollama

```bash
ollama run qwen2.5:1.5b
```

Keep this terminal open.

### Step 2 — Run App

```bash
streamlit run streamlit_app.py
```

### Step 3 — In the browser

1. Upload Job Description (TXT / PDF / DOCX)
2. Upload Resumes (PDF / DOCX / TXT) — multiple supported
3. Upload LinkedIn files (JSON / PDF / TXT) — optional
4. Click **🚀 Run AI Shortlisting**
5. Review ranked candidates, scores, and detailed analysis
6. Set Recruiter Decision (Shortlist / Hold / Reject) and add notes
7. Download reports (JSON / TXT / HTML)

---

## Scoring Rubric

| Dimension | Weight | 0 – Poor | 5 – Average | 10 – Excellent |
|---|---|---|---|---|
| Skills Match | 30% | < 30% skills match | 50–70% skills match | > 85% skills match |
| Experience Relevance | 25% | Unrelated domain | Adjacent domain | Exact domain & seniority |
| Education & Certs | 15% | Does not meet minimum | Meets minimum | Exceeds + extra certs |
| Project / Portfolio | 20% | No evidence | 1–2 generic projects | Strong relevant portfolio |
| Communication Quality | 10% | Poor structure/grammar | Adequate clarity | Crisp, structured, impactful |

**Recommendation thresholds:**

| Score | Recommendation |
|---|---|
| ≥ 7.0 | ✅ Hire |
| ≥ 4.5 | 🟡 Maybe |
| < 4.5 | ❌ No Hire |

---

## Sample Output

See `sample_output/` folder for:
- `shortlist_report.json` — full JSON report with dimension scores
- `shortlist_report.txt` — human-readable ranked report
- `shortlist_report.html` — HTML report

**Example run — TechCorp India · Senior ML Engineer (5 candidates):**

| Rank | Candidate | Score | Recommendation |
|---|---|---|---|
| #1 | Sneha Dhir | 8.15 / 10 | ✅ Hire |
| #2 | Arjun Mehta | 7.25 / 10 | ✅ Hire |
| #3 | Rahul Sharma | 6.95 / 10 | 🟡 Maybe |
| #4 | Priya Nair | 6.19 / 10 | 🟡 Maybe |
| #5 | Ravi Kumar | 5.00 / 10 | 🟡 Maybe |

---

## Project Structure

```
AI-HR-Shortlisting-Agent/
│
├── streamlit_app.py          # Main Streamlit UI
├── requirements.txt
├── .env.example              # Environment variable template
├── README.md
│
├── docs/
│   └── AI_HR_Shortlisting_Agent.pptx   # Project presentation
│
├── llm/
│   └── llm_engine.py         # Ollama LLM wrapper
│
├── parsers/
│   ├── jd_parser.py          # Job Description parser
│   ├── resume_parser.py      # Resume PDF/DOCX/TXT parser
│   └── linkedin_parser.py    # LinkedIn JSON/PDF/TXT parser
│
├── scoring/
│   ├── scorer.py             # 5-dimension scoring engine
│   ├── ranking.py            # Candidate ranker
│   └── semantic_matcher.py   # SentenceTransformers matcher
│
├── utils/
│   └── helpers.py            # Report generator (JSON/TXT/HTML)
│
├── temp/                     # Temporary upload storage (auto-cleared)
│   ├── jd/
│   ├── resumes/
│   └── linkedin/
│
├── reports/                  # Generated reports output
│
└── sample_output/            # Sample reports for submission
    ├── shortlist_report.json
    ├── shortlist_report.txt
    └── shortlist_report.html
```

---

## Author

**Sneha Dhir**  
B.Tech CSE (AI/ML) — UPES Dehradun

---

## License

This project is for educational and demonstration purposes as part of the AI Enablement Internship.