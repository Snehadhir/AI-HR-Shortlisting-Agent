
"""
parsers/linkedin_parser.py
--------------------------
LinkedIn Profile Parser
UPDATED VERSION
(JSON + PDF + DOCX + TXT)
"""

import json
from pathlib import Path

from parsers.resume_parser import (
    CandidateProfile,
    ResumeParser
)


class LinkedInParser:

    def __init__(self):

        self.resume_parser = ResumeParser()

    # ─────────────────────────────────────────
    # JSON LINKEDIN PARSER
    # ─────────────────────────────────────────

    def parse_json_file(
        self,
        filepath: str
    ) -> CandidateProfile:

        filepath = Path(filepath)

        data = json.loads(

            filepath.read_text(
                encoding="utf-8"
            )
        )

        return self.parse_dict(data)

    # ─────────────────────────────────────────
    # JSON → PROFILE
    # ─────────────────────────────────────────

    def parse_dict(
        self,
        data: dict
    ) -> CandidateProfile:

        full_name = data.get(
            "full_name",
            "Unknown Candidate"
        )

        headline = data.get(
            "headline",
            ""
        )

        location = data.get(
            "location",
            ""
        )

        summary = data.get(
            "summary",
            ""
        )

        skills = data.get(
            "skills",
            []
        )

        experience = data.get(
            "experience",
            []
        )

        education = data.get(
            "education",
            []
        )

        projects = data.get(
            "projects",
            []
        )

        # ─────────────────────────────────────
        # EXPERIENCE
        # ─────────────────────────────────────

        experience_lines = []

        total_years = 0.0

        for exp in experience:

            role = exp.get(
                "role",
                ""
            )

            company = exp.get(
                "company",
                ""
            )

            years = exp.get(
                "years",
                ""
            )

            desc = exp.get(
                "description",
                ""
            )

            experience_lines.append(

                f"{role} at {company} "
                f"({years}) : {desc}"
            )

            # SIMPLE YEAR ESTIMATION

            if "2022" in years:
                total_years += 3

            elif "2021" in years:
                total_years += 4

            elif "2020" in years:
                total_years += 5

            elif "2019" in years:
                total_years += 6

        experience_text = " | ".join(
            experience_lines
        )

        # ─────────────────────────────────────
        # EDUCATION
        # ─────────────────────────────────────

        education_lines = []

        for edu in education:

            degree = edu.get(
                "degree",
                ""
            )

            college = edu.get(
                "college",
                ""
            )

            education_lines.append(

                f"{degree} from {college}"
            )

        education_text = " | ".join(
            education_lines
        )

        # ─────────────────────────────────────
        # PROJECTS
        # ─────────────────────────────────────

        project_lines = []

        for proj in projects:

            name = proj.get(
                "name",
                ""
            )

            desc = proj.get(
                "description",
                ""
            )

            project_lines.append(

                f"{name}: {desc}"
            )

        projects_text = " | ".join(
            project_lines
        )

        # ─────────────────────────────────────
        # AI SUMMARY
        # ─────────────────────────────────────

        ai_summary = (

            f"{full_name} is an "
            f"AI/ML professional with "
            f"{round(total_years, 1)} years "
            f"of experience in "
            f"{headline}. "
            f"Skilled in "
            f"{', '.join(skills[:6])}."
        )

        # ─────────────────────────────────────
        # CURRENT COMPANY
        # ─────────────────────────────────────

        current_company = ""

        if experience:

            current_company = (

                experience[0].get(
                    "company",
                    ""
                )
            )

        # ─────────────────────────────────────
        # RETURN PROFILE
        # ─────────────────────────────────────

        return CandidateProfile(

            source_file=str(full_name),

            full_name=full_name,

            headline=headline,

            location=location,

            current_company=current_company,

            summary=summary,

            total_experience_years=
                round(total_years, 1),

            skills=skills,

            certifications=[],

            experience_text=experience_text,

            education_text=education_text,

            projects_text=projects_text,

            ai_generated_summary=ai_summary,

            raw_text=json.dumps(
                data,
                indent=2
            ),
        )

    # ─────────────────────────────────────────
    # PARSE BATCH
    # ─────────────────────────────────────────

    def parse_batch(
        self,
        folder: str
    ) -> list:

        folder = Path(folder)

        if not folder.exists():

            print(
                f"Folder not found: {folder}"
            )

            return []

        # SUPPORT ALL FILE TYPES

        files = (

            list(folder.glob("*.json"))

            + list(folder.glob("*.pdf"))

            + list(folder.glob("*.docx"))

            + list(folder.glob("*.txt"))
        )

        if not files:

            print(
                f"No LinkedIn files found in {folder}"
            )

            return []

        profiles = []

        for file in files:

            try:

                # JSON LINKEDIN EXPORT

                if file.suffix.lower() == ".json":

                    profile = self.parse_json_file(
                        str(file)
                    )

                # PDF / DOCX / TXT

                else:

                    profile = self.resume_parser.parse(
                        str(file)
                    )

                profiles.append(profile)

                print(

                    f"✓ Parsed LinkedIn "
                    f"Profile → "
                    f"{profile.full_name}"
                )

            except Exception as e:

                print(

                    f"✗ Failed: "
                    f"{file.name} — {e}"
                )

        return profiles


# ALSO CREATE THIS FILE

## utils/file_reader.py


import pdfplumber
from docx import Document


def read_txt(file_path):

    with open(file_path, 'r', encoding='utf-8') as f:

        return f.read()


def read_pdf(file_path):

    text = ""

    with pdfplumber.open(file_path) as pdf:

        for page in pdf.pages:

            extracted = page.extract_text()

            if extracted:

                text += extracted + "\n"

    return text


def read_docx(file_path):

    doc = Document(file_path)

    text = "\n".join(
        [para.text for para in doc.paragraphs]
    )

    return text


def extract_text(file_path):

    if file_path.endswith(".txt"):

        return read_txt(file_path)

    elif file_path.endswith(".pdf"):

        return read_pdf(file_path)

    elif file_path.endswith(".docx"):

        return read_docx(file_path)

    else:

        return ""
