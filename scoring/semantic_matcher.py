"""
scoring/semantic_matcher.py
---------------------------
Semantic similarity engine
"""

from sentence_transformers import (
    SentenceTransformer,
    util
)


class SemanticMatcher:

    def __init__(self):

        # LIGHTWEIGHT CPU MODEL
        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    # ─────────────────────────────────────────
    # TEXT SIMILARITY
    # ─────────────────────────────────────────

    def similarity(
        self,
        text1: str,
        text2: str
    ) -> float:

        if not text1 or not text2:
            return 0.0

        emb1 = self.model.encode(
            text1,
            convert_to_tensor=True
        )

        emb2 = self.model.encode(
            text2,
            convert_to_tensor=True
        )

        score = util.cos_sim(
            emb1,
            emb2
        ).item()

        return round(score, 4)

    # ─────────────────────────────────────────
    # RESUME ↔ JD MATCH
    # ─────────────────────────────────────────

    def match_resume_to_jd(
        self,
        candidate,
        jd
    ) -> float:

        resume_text = " ".join([

            candidate.summary or "",

            candidate.projects_text or "",

            candidate.experience_text or "",

            " ".join(candidate.skills or [])
        ])

        jd_text = " ".join([

            jd.title or "",

            jd.industry_domain or "",

            " ".join(jd.required_skills or []),

            " ".join(jd.preferred_skills or [])
        ])

        return self.similarity(
            resume_text,
            jd_text
        )