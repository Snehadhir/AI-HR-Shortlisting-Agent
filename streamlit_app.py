"""
streamlit_app.py
----------------
AI HR Shortlisting Agent
FINAL CLEAN PROFESSIONAL VERSION
"""

import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from pathlib import Path

from llm.llm_engine import LLMEngine
from parsers.jd_parser import JDParser
from parsers.resume_parser import ResumeParser
from parsers.linkedin_parser import LinkedInParser

from scoring.scorer import Scorer
from scoring.ranking import Ranker

from utils.helpers import ReportGenerator


# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────

st.set_page_config(
    page_title="AI HR Shortlisting Agent",
    page_icon="🤖",
    layout="wide"
)

# ─────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────

st.markdown(
    """
    <style>

    .stApp {
        background: linear-gradient(135deg, #dff6ff, #b8e8fc);
        color: black;
    }

    html, body, [class*="css"] {
        color: black;
    }

    section[data-testid="stSidebar"] {
        display: none;
    }

    .main-title {
        text-align: center;
        font-size: 65px;
        font-weight: 800;
        color: black;
        margin-top: 20px;
    }

    .sub-title {
        text-align: center;
        font-size: 28px;
        color: #333;
        margin-bottom: 40px;
    }

    .upload-box {
        background: white;
        padding: 40px;
        border-radius: 25px;
        box-shadow: 0px 8px 25px rgba(0,0,0,0.15);
        margin-bottom: 40px;
    }

    .score-card {
        background: white;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0px 6px 18px rgba(0,0,0,0.15);
        margin-bottom: 25px;
    }

    .stButton>button {
        background-color: #ffd93d;
        color: black;
        border-radius: 12px;
        border: none;
        font-size: 20px;
        font-weight: bold;
        padding: 14px 20px;
        width: 100%;
    }

    .stButton>button:hover {
        background-color: #ffcc00;
        color: black;
    }

    [data-testid="stFileUploader"] label {
        color: #003366 !important;
        font-weight: bold !important;
        font-size: 20px !important;
    }

    [data-testid="stFileUploaderFileName"] {
        color: #003366 !important;
        font-weight: bold !important;
    }

    [data-testid="stBaseButton-secondary"] {
        background-color: white !important;
        color: black !important;
        border-radius: 10px !important;
        border: 1px solid #cccccc !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ─────────────────────────────────────────
# TITLE
# ─────────────────────────────────────────

st.markdown(
    """
    <div class="main-title">
    🤖 AI HR Shortlisting Agent
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="sub-title">
    AI-Powered Resume Screening & Candidate Ranking Dashboard
    </div>
    """,
    unsafe_allow_html=True
)

# ─────────────────────────────────────────
# TEMP FOLDERS
# ─────────────────────────────────────────

TEMP_JD = Path("temp/jd")
TEMP_RESUMES = Path("temp/resumes")
TEMP_LINKEDIN = Path("temp/linkedin")

TEMP_JD.mkdir(parents=True, exist_ok=True)
TEMP_RESUMES.mkdir(parents=True, exist_ok=True)
TEMP_LINKEDIN.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────
# UPLOAD SECTION
# ─────────────────────────────────────────

with st.container():

    st.markdown('<div class="upload-box">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📄 Job Description")
        jd_file = st.file_uploader(
            "Upload JD",
            type=["txt", "pdf", "docx"]
        )

    with col2:
        st.subheader("📑 Resumes")
        resume_files = st.file_uploader(
            "Upload Resumes",
            type=["pdf", "txt", "docx"],
            accept_multiple_files=True
        )

    with col3:
        st.subheader("🔗 LinkedIn Files")
        linkedin_files = st.file_uploader(
            "Upload LinkedIn",
            type=["json", "pdf", "docx", "txt"],
            accept_multiple_files=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])

    with c2:
        run_button = st.button("🚀 Run AI Shortlisting")

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────

if run_button:

    if not jd_file:
        st.error("Please upload a Job Description.")
        st.stop()

    # CLEAR TEMP FILES SAFELY
    for folder in [TEMP_JD, TEMP_RESUMES, TEMP_LINKEDIN]:
        folder.mkdir(parents=True, exist_ok=True)
        for file in folder.glob("*"):
            try:
                if file.is_file():
                    file.unlink()
            except Exception as e:
                print(f"Could not delete {file}: {e}")

    # SAVE JD
    jd_path = TEMP_JD / jd_file.name
    with open(jd_path, "wb") as f:
        f.write(jd_file.read())

    # SAVE RESUMES
    for file in resume_files:
        file_path = TEMP_RESUMES / file.name
        with open(file_path, "wb") as f:
            f.write(file.read())

    # SAVE LINKEDIN FILES
    for file in linkedin_files:
        file_path = TEMP_LINKEDIN / file.name
        with open(file_path, "wb") as f:
            f.write(file.read())

    # AI MODEL
    with st.spinner("Initializing AI Model..."):
        engine = LLMEngine(model="qwen2.5:1.5b")

    st.success("✅ AI Model Connected")

    # PARSE JD
    with st.spinner("Parsing Job Description..."):
        jd_parser = JDParser()
        jd = jd_parser.parse_file(str(jd_path))

    st.success(f"✅ Parsed JD: {jd.title}")

    # PARSE CANDIDATES
    candidates = []

    if resume_files:
        with st.spinner("Parsing Resumes..."):
            resume_parser = ResumeParser()
            parsed_resumes = resume_parser.parse_batch(str(TEMP_RESUMES))
            candidates.extend(parsed_resumes)

    if linkedin_files:
        with st.spinner("Parsing LinkedIn Profiles..."):
            li_parser = LinkedInParser()
            parsed_li = li_parser.parse_batch(str(TEMP_LINKEDIN))
            candidates.extend(parsed_li)

    # REMOVE EXACT DUPLICATES ONLY
    unique_candidates = {}
    for candidate in candidates:
        candidate_key = (
            getattr(candidate, "full_name", "Unknown")
            +
            getattr(candidate, "source_file", "")
        )
        unique_candidates[candidate_key] = candidate
    candidates = list(unique_candidates.values())

    # NO CANDIDATES
    if not candidates:
        st.error("No candidates loaded.")
        st.stop()

    st.success(f"✅ Loaded {len(candidates)} Candidate(s)")

    # AI SCORING
    with st.spinner("Running AI Resume Matching..."):
        scorer = Scorer(engine)
        results = []
        for candidate in candidates:
            result = scorer.score(candidate, jd)
            result.ats_score = round(result.total_score * 10, 2)
            results.append(result)

    # RANKING
    ranker = Ranker()
    ranked = ranker.rank(results)

    # REPORTS
    reporter = ReportGenerator()
    report_paths = reporter.generate_all(ranked, jd)

    # ── Persist results in session_state so reruns don't wipe them ──
    st.session_state["ranked"] = ranked
    st.session_state["report_paths"] = report_paths
    st.session_state["pipeline_done"] = True


# ─────────────────────────────────────────
# RESULTS — rendered from session_state
# (survives form submits and other reruns)
# ─────────────────────────────────────────

if st.session_state.get("pipeline_done"):

    ranked = st.session_state["ranked"]
    report_paths = st.session_state["report_paths"]

    st.markdown("## 🏆 Ranked Candidates")

    for i, r in enumerate(ranked, 1):

        ats_score = round(r.total_score * 10, 2)

        if ats_score >= 80:
            gauge_color = "green"
        elif ats_score >= 60:
            gauge_color = "orange"
        else:
            gauge_color = "red"

        # ── Candidate header card ──
        st.markdown(
            f"""
            <div class="score-card">
            <h2>#{i} {r.candidate_name}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ── Gauge chart ──
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=ats_score,
                title={'text': "ATS Match Score %"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': gauge_color},
                    'bgcolor': "white",
                    'steps': [
                        {'range': [0, 50],  'color': '#ffb3b3'},
                        {'range': [50, 75], 'color': '#ffe680'},
                        {'range': [75, 100], 'color': '#b3ffb3'}
                    ]
                }
            )
        )
        fig.update_layout(
            height=320,
            paper_bgcolor="white",
            font={'color': "black"}
        )
        st.plotly_chart(fig, use_container_width=True, key=f"plot_chart_{i}")

        # ── Score metrics ──
        col1, col2 = st.columns(2)
        with col1:
            st.metric("AI Score", f"{r.total_score}/10")
        with col2:
            st.metric("ATS Score", f"{ats_score}%")

        # ── AI recommendation ──
        st.markdown(f"### 🤖 Recommendation: {r.recommendation}")

        # ── Default index for selectbox ──
        if ats_score >= 75:
            default_index = 0
        elif ats_score >= 50:
            default_index = 1
        else:
            default_index = 2

        # ── Recruiter form ──
        with st.form(key=f"recruiter_form_{i}"):
            decision = st.selectbox(
                "👨‍💼 Recruiter Decision",
                ["Shortlist", "Hold", "Reject"],
                index=default_index,
                key=f"decision_{i}"
            )
            notes = st.text_area(
                "📝 Recruiter Notes",
                placeholder="Add recruiter comments here...",
                key=f"notes_{i}"
            )
            submitted = st.form_submit_button("✅ Save Recruiter Decision")
            if submitted:
                # Save explicitly so summary table survives future reruns
                st.session_state[f"saved_decision_{i}"] = decision
                st.session_state[f"saved_notes_{i}"] = notes
                st.success(f"Decision saved for {r.candidate_name}")

        # ── Detailed Analysis ──
        with st.expander(f"📋 View Detailed Analysis — {r.candidate_name}"):

            st.markdown("## 📄 Candidate Summary")
            st.write(r.final_reasoning)
            st.markdown("---")

            st.markdown("## 📊 Dimension-wise Scoring")

            dim_source = getattr(r, "dimension_scores", None)

            if dim_source and isinstance(dim_source, list) and len(dim_source) > 0:
                dim_rows = []
                for dim in dim_source:
                    dim_rows.append({
                        "Dimension":     dim.label,
                        "Weight":        f"{int(dim.weight * 100)}%",
                        "Score /10":     dim.raw_score,
                        "Weighted":      dim.weighted_score,
                        "Justification": dim.justification
                    })
                score_df = pd.DataFrame(dim_rows)
            else:
                score_df = pd.DataFrame({
                    "Dimension":     ["Skills Match", "Experience", "Projects", "Education", "Communication"],
                    "Weight":        ["30%", "25%", "20%", "15%", "10%"],
                    "Score /10":     [0, 0, 0, 0, 0],
                    "Weighted":      [0, 0, 0, 0, 0],
                    "Justification": ["No data", "No data", "No data", "No data", "No data"]
                })

            st.dataframe(score_df, use_container_width=True)
            st.markdown("---")

            saved_decision = st.session_state.get(f"saved_decision_{i}", decision)
            saved_notes    = st.session_state.get(f"saved_notes_{i}", notes)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**🤖 AI Recommendation:** {r.recommendation}")
                st.markdown(f"**📊 ATS Score:** {ats_score}%")
            with col_b:
                st.markdown(f"**👨‍💼 Recruiter Decision:** {saved_decision}")
                if saved_notes:
                    st.markdown(f"**📝 Notes:** {saved_notes}")

        st.markdown("---")

    # ─────────────────────────────────────────
    # FINAL SUMMARY TABLE
    # ─────────────────────────────────────────

    st.header("📋 Final Recruiter Decisions")

    summary_data = []
    for i, r in enumerate(ranked, 1):
        rec_dec = st.session_state.get(
            f"saved_decision_{i}",
            st.session_state.get(f"decision_{i}", "Not Selected")
        )
        summary_data.append({
            "Rank":               i,
            "Candidate":          r.candidate_name,
            "ATS Score":          f"{round(r.total_score * 10, 2)}%",
            "AI Recommendation":  r.recommendation,
            "Recruiter Decision": rec_dec
        })

    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)

    # ─────────────────────────────────────────
    # DOWNLOAD REPORTS
    # ─────────────────────────────────────────

    st.header("📥 Download Reports")

    for fmt, path in report_paths.items():
        with open(path, "rb") as f:
            st.download_button(
                label=f"Download {fmt.upper()}",
                data=f,
                file_name=os.path.basename(path),
                mime="application/octet-stream"
            )

    st.success("✅ AI Pipeline Complete")