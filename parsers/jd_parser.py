"""
parsers/jd_parser.py
--------------------
FINAL Deterministic JD Parser
"""

import json
import re

from dataclasses import dataclass, field, asdict
from pathlib import Path

from llm.llm_engine import LLMEngine


# ─────────────────────────────────────────────
# DATA MODEL
# ─────────────────────────────────────────────

@dataclass
class ParsedJD:

    title: str

    company: str

    location: str

    min_experience_years: int

    max_experience_years: int

    required_skills: list[str]

    preferred_skills: list[str]

    education_requirement: str

    key_responsibilities: list[str]

    industry_domain: str

    seniority_level: str

    raw_text: str = field(repr=False)


# ─────────────────────────────────────────────
# PROMPT
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """
You are an HR analyst.

Extract structured information from the Job Description.

STRICT RULES:
- Return ONLY valid JSON
- No markdown
- No explanations
- No comments
- No extra text
- Keep output concise
- Keep output deterministic
- Do not hallucinate

Return EXACTLY this JSON:

{
  "title": "string",
  "company": "string",
  "location": "string",
  "min_experience_years": 0,
  "max_experience_years": 0,
  "required_skills": ["string"],
  "preferred_skills": ["string"],
  "education_requirement": "string",
  "key_responsibilities": ["string"],
  "industry_domain": "string",
  "seniority_level": "Junior"
}
"""


# ─────────────────────────────────────────────
# JD PARSER
# ─────────────────────────────────────────────

class JDParser:

    def __init__(self):

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

        # NORMALIZE SPACES
        json_text = re.sub(
            r"\s+",
            " ",
            json_text
        )

        try:

            return json.loads(json_text)

        except Exception as e:

            print("\nBROKEN JD JSON:\n")
            print(json_text)

            raise ValueError(
                f"\nJSON Parse Failed:\n{e}\n"
            )

    # ─────────────────────────────────────────

    def parse_text(
        self,
        jd_text: str
    ) -> ParsedJD:

        # FIXED INPUT SIZE
        jd_text = jd_text[:1200]

        output = self.engine.chat(

            SYSTEM_PROMPT,

            f"""
Extract structured JD information.

JD:
{jd_text}
"""
        )

        if not output.strip():

            raise ValueError(
                "Qwen returned empty JD output"
            )

        data = self.extract_json(output)

        return ParsedJD(

            title=data.get(
                "title",
                "Unknown Role"
            ),

            company=data.get(
                "company",
                "Unknown Company"
            ),

            location=data.get(
                "location",
                "Not specified"
            ),

            min_experience_years=int(

                data.get(
                    "min_experience_years",
                    0
                )
            ),

            max_experience_years=int(

                data.get(
                    "max_experience_years",
                    0
                )
            ),

            required_skills=data.get(
                "required_skills",
                []
            ),

            preferred_skills=data.get(
                "preferred_skills",
                []
            ),

            education_requirement=data.get(
                "education_requirement",
                "Not specified"
            ),

            key_responsibilities=data.get(
                "key_responsibilities",
                []
            ),

            industry_domain=data.get(
                "industry_domain",
                "Not specified"
            ),

            seniority_level=data.get(
                "seniority_level",
                "Not specified"
            ),

            raw_text=jd_text,
        )

    # ─────────────────────────────────────────

    def parse_file(
        self,
        filepath: str
    ) -> ParsedJD:

        filepath = Path(filepath)

        if not filepath.exists():

            raise FileNotFoundError(
                f"JD file not found: {filepath}"
            )

        text = filepath.read_text(
            encoding="utf-8"
        )

        if not text.strip():

            raise ValueError(
                "JD file is empty"
            )

        return self.parse_text(text)

    # ─────────────────────────────────────────

    def to_dict(
        self,
        jd: ParsedJD
    ) -> dict:

        data = asdict(jd)

        data.pop(
            "raw_text",
            None
        )

        return data