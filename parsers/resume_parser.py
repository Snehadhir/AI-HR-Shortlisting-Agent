"""
parsers/resume_parser.py
------------------------
FINAL Deterministic Resume Parser
(PDF / DOCX / TXT)
"""

import json
import re
from utils.file_reader import extract_text
from dataclasses import dataclass, field
from pathlib import Path

from llm.llm_engine import LLMEngine


# ─────────────────────────────────────────────
# DATA MODEL
# ─────────────────────────────────────────────

@dataclass
class CandidateProfile:

    source_file: str
    full_name: str
    headline: str
    location: str
    current_company: str
    summary: str
    total_experience_years: float
    skills: list[str]
    certifications: list[str]
    experience_text: str
    education_text: str
    projects_text: str

    ai_generated_summary: str = ""

    raw_text: str = field(
        repr=False,
        default=""
    )


# ─────────────────────────────────────────────
# TEXT EXTRACTION
# ─────────────────────────────────────────────

def extract_text(filepath: str) -> str:

    ext = Path(filepath).suffix.lower()

    # ─────────────────────────────────────────
    # PDF
    # ─────────────────────────────────────────

    if ext == ".pdf":

        try:

            import fitz

            doc = fitz.open(filepath)

            text_parts = []

            max_pages = min(len(doc), 2)

            for i in range(max_pages):

                page = doc[i]

                blocks = page.get_text("blocks")

                for block in blocks:

                    block_text = block[4]

                    if block_text.strip():

                        text_parts.append(
                            block_text.strip()
                        )

            doc.close()

            text = "\n".join(text_parts)

            # CLEANING
            text = re.sub(
                r"\s+",
                " ",
                text
            )

            text = re.sub(
                r"[^a-zA-Z0-9@+.#,/():\-\n ]",
                " ",
                text
            )

            text = re.sub(
                r" +",
                " ",
                text
            )

            # FIXED SIZE
            text = text[:1800]

            return text.strip()

        except ImportError:

            raise ImportError(
                "Install PyMuPDF:\n"
                "pip install PyMuPDF"
            )

    # ─────────────────────────────────────────
    # DOCX
    # ─────────────────────────────────────────

    elif ext == ".docx":

        try:

            from docx import Document

            doc = Document(filepath)

            text = "\n".join(

                p.text

                for p in doc.paragraphs

                if p.text.strip()
            )

            return text[:1000].strip()

        except ImportError:

            raise ImportError(
                "Install python-docx:\n"
                "pip install python-docx"
            )

    # ─────────────────────────────────────────
    # TXT / MD
    # ─────────────────────────────────────────

    elif ext in (".txt", ".md"):

        text = Path(filepath).read_text(
            encoding="utf-8"
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text[:1000].strip()

    # ─────────────────────────────────────────
    # UNSUPPORTED
    # ─────────────────────────────────────────

    else:

        raise ValueError(
            f"Unsupported file format: {ext}"
        )


# ─────────────────────────────────────────────
# PROMPT
# ─────────────────────────────────────────────

EXTRACT_SYSTEM = """
You are an expert HR resume parser.

Extract structured information from the resume.

STRICT RULES:
- Return ONLY valid JSON
- No markdown
- No explanations
- No comments
- No extra text
- Keep outputs concise
- Keep outputs deterministic
- Do not hallucinate
- If something is missing write "Not specified"

Return EXACTLY this JSON:

{
  "full_name": "string",
  "headline": "string",
  "location": "string",
  "current_company": "string",
  "summary": "string",
  "total_experience_years": 0.0,
  "skills": ["string"],
  "certifications": ["string"],
  "experience_text": "string",
  "education_text": "string",
  "projects_text": "string",
  "ai_generated_summary": "string"
}
"""


# ─────────────────────────────────────────────
# RESUME PARSER
# ─────────────────────────────────────────────

class ResumeParser:

    def __init__(self):

        # DETERMINISTIC MODEL
        self.engine = LLMEngine(
            model="qwen2.5:1.5b"
        )

    # ─────────────────────────────────────────

    def clean_output(self, text: str):

        if not text:
            return ""

        text = re.sub(
            r"```json",
            "",
            text
        )

        text = re.sub(
            r"```",
            "",
            text
        )

        return text.strip()

    # ─────────────────────────────────────────

    def extract_json(self, text: str):

        text = self.clean_output(text)

        if not text.strip():

            raise ValueError(
                "LLM returned empty output"
            )

        # FIND JSON
        start = text.find("{")

        end = text.rfind("}") + 1

        if start == -1 or end == 0:

            raise ValueError(
                f"Could not find JSON in output:\n{text}"
            )

        json_text = text[start:end]

        # FIX TRAILING COMMAS
        json_text = re.sub(
            r",\s*}",
            "}",
            json_text
        )

        json_text = re.sub(
            r",\s*]",
            "]",
            json_text
        )

        # REMOVE CONTROL CHARS
        json_text = re.sub(
            r"[\x00-\x1f\x7f]",
            " ",
            json_text
        )

        # NORMALIZE
        json_text = re.sub(
            r"\s+",
            " ",
            json_text
        )

        try:

            return json.loads(json_text)

        except Exception as e:

            print("\nBROKEN JSON:\n")
            print(json_text)

            raise ValueError(
                f"\nJSON Parse Failed:\n{e}\n"
            )

    # ─────────────────────────────────────────

    def save_parsed_json(
        self,
        filepath: str,
        data: dict
    ):

        parsed_dir = Path(
            "data/parsed_resumes"
        )

        parsed_dir.mkdir(
            exist_ok=True
        )

        output_file = (
            parsed_dir /
            f"{Path(filepath).stem}.json"
        )

        output_file.write_text(

            json.dumps(
                data,
                indent=2
            ),

            encoding="utf-8"
        )

    # ─────────────────────────────────────────

    def parse(
        self,
        filepath: str
    ) -> CandidateProfile:

        print(
            f"\nParsing Resume: {filepath}"
        )

        raw_text = extract_text(filepath)

        if not raw_text.strip():

            raise ValueError(
                f"Could not extract text from "
                f"{filepath}"
            )

        output = self.engine.chat(

            EXTRACT_SYSTEM,

            f"""
Extract resume data.

Resume:
{raw_text}
"""
        )

        data = self.extract_json(output)

        self.save_parsed_json(
            filepath,
            data
        )

        return CandidateProfile(

            source_file=str(filepath),

            full_name=data.get(
                "full_name",
                Path(filepath).stem
            ),

            headline=data.get(
                "headline",
                ""
            ),

            location=data.get(
                "location",
                ""
            ),

            current_company=data.get(
                "current_company",
                ""
            ),

            summary=data.get(
                "summary",
                ""
            ),

            total_experience_years=float(

                data.get(
                    "total_experience_years",
                    0
                )
            ),

            skills=data.get(
                "skills",
                []
            ),

            certifications=data.get(
                "certifications",
                []
            ),

            experience_text=data.get(
                "experience_text",
                ""
            ),

            education_text=data.get(
                "education_text",
                ""
            ),

            projects_text=data.get(
                "projects_text",
                ""
            ),

            ai_generated_summary=data.get(
                "ai_generated_summary",
                ""
            ),

            raw_text=raw_text,
        )

    # ─────────────────────────────────────────

    def parse_batch(
        self,
        folder: str
    ) -> list[CandidateProfile]:

        folder_path = Path(folder)

        files = (

            list(folder_path.glob("*.pdf"))

            + list(folder_path.glob("*.docx"))

            + list(folder_path.glob("*.txt"))
        )

        if not files:

            raise ValueError(
                f"No resume files found in "
                f"{folder}"
            )

        profiles = []

        for f in files:

            try:

                if not f.exists():

                    print(
                        f"✗ Missing file: {f.name}"
                    )

                    continue

                if f.stat().st_size == 0:

                    print(
                        f"✗ Empty file: {f.name}"
                    )

                    continue

                profile = self.parse(str(f))

                profiles.append(profile)

                print(
                    f"✓ Parsed: "
                    f"{f.name} → "
                    f"{profile.full_name}"
                )

            except Exception as e:

                print(
                    f"✗ Failed: "
                    f"{f.name} — {e}"
                )

        return profiles