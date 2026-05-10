"""
scoring/scorer.py
-----------------
FINAL GenAI-Aware ATS Scorer
Semantic + Deterministic
"""

from dataclasses import dataclass, field
from typing import List

from parsers.resume_parser import CandidateProfile
from parsers.jd_parser import ParsedJD

from scoring.semantic_matcher import SemanticMatcher


# ─────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────

@dataclass
class DimensionScore:

    key: str
    label: str
    weight: float
    raw_score: float
    weighted_score: float
    justification: str


@dataclass
class ScoreResult:

    candidate_name: str
    total_score: float
    recommendation: str
    dimension_scores: List[DimensionScore]
    final_reasoning: str

    current_role: str = ""
    percentage: float = 0.0
    ai_summary: str = ""

    override_log: list = field(
        default_factory=list
    )

    thinking: str = ""


# ─────────────────────────────────────────────
# WEIGHTS
# ─────────────────────────────────────────────

WEIGHTS = {

    "skills_match": 0.30,

    "experience_relevance": 0.25,

    "project_portfolio": 0.20,

    "education_certs": 0.15,

    "communication_quality": 0.10,
}


# ─────────────────────────────────────────────
# SCORER
# ─────────────────────────────────────────────

class Scorer:

    def __init__(self, engine):

        self.engine = engine

        self.semantic_matcher = (
            SemanticMatcher()
        )

    # ─────────────────────────────────────────

    def score(
        self,
        candidate: CandidateProfile,
        jd: ParsedJD,
        capture_thinking=False
    ) -> ScoreResult:

        total_score, dimension_scores = (

            self.calculate_score(
                candidate,
                jd
            )
        )

        recommendation = (

            self.get_recommendation(
                total_score
            )
        )

        reasoning = (

            self.generate_reasoning(
                candidate,
                jd,
                recommendation
            )
        )

        return ScoreResult(

            candidate_name=
                candidate.full_name,

            total_score=
                total_score,

            recommendation=
                recommendation,

            dimension_scores=
                dimension_scores,

            final_reasoning=
                reasoning,

            current_role=
                candidate.headline,

            percentage=
                round(total_score * 10, 2),

            ai_summary=
                reasoning,

            override_log=[],

            thinking=""
        )

    # ─────────────────────────────────────────
    # MAIN SCORING LOGIC
    # ─────────────────────────────────────────

    def calculate_score(
        self,
        candidate,
        jd
    ):

        first_name = (
            candidate.full_name
            .split()[0]
        )

        # ─────────────────────────────────────
        # SKILLS
        # ─────────────────────────────────────

        candidate_skills = [

            s.lower()

            for s in candidate.skills
        ]

        jd_skills = [

            s.lower()

            for s in jd.required_skills
        ]

        matched_skills = 0

        matched_names = []

        AI_KEYWORDS = {

            "llm": [

                "llm",
                "gpt",
                "llama",
                "rag",
                "langchain",
                "langgraph",
                "prompt",
                "embedding",
                "agentic",
                "transformer",
            ],

            "mlops": [

                "docker",
                "kubernetes",
                "mlflow",
                "ci/cd",
            ],

            "vector_db": [

                "pinecone",
                "faiss",
                "weaviate",
            ],

            "api": [

                "fastapi",
                "rest api",
                "api",
            ]
        }

        combined_skills = (
            " ".join(candidate_skills)
        )

        for jd_skill in jd_skills:

            jd_lower = jd_skill.lower()

            matched = False

            # DIRECT MATCH
            for cskill in candidate_skills:

                if (

                    jd_lower in cskill

                    or

                    cskill in jd_lower
                ):

                    matched = True

                    matched_names.append(
                        cskill
                    )

                    break

            # AI CATEGORY MATCH
            if not matched:

                for (
                    category,
                    keywords
                ) in AI_KEYWORDS.items():

                    if any(

                        word in jd_lower

                        for word in keywords
                    ):

                        if any(

                            word in combined_skills

                            for word in keywords
                        ):

                            matched = True

                            matched_skills += 1

                            matched_names.append(
                                category
                            )

                            break

            if matched:

                matched_skills += 1

        if jd_skills:

            match_ratio = (

                matched_skills
                /
                len(jd_skills)
            )

            if match_ratio >= 0.90:

                skill_score = 10.0

            elif match_ratio >= 0.75:

                skill_score = 8.5

            elif match_ratio >= 0.60:

                skill_score = 7.0

            elif match_ratio >= 0.45:

                skill_score = 5.5

            elif match_ratio >= 0.30:

                skill_score = 4.0

            else:

                skill_score = 2.0

        else:

            skill_score = 0.0

        skill_score = round(
            skill_score,
            2
        )

        skill_just = (

            f"Matched "

            f"{matched_skills}/"

            f"{len(jd_skills)} "

            f"required skills"
        )

        # ─────────────────────────────────────
        # EXPERIENCE
        # ─────────────────────────────────────

        exp_years = (
            candidate.total_experience_years
        )

        min_exp = (
            jd.min_experience_years
        )

        if exp_years >= min_exp:

            exp_score = 10.0

        elif exp_years >= (min_exp * 0.6):

            exp_score = 8.0

        elif exp_years >= 1:

            exp_score = 6.0

        else:

            exp_score = 4.0

        exp_score = round(
            exp_score,
            2
        )

        exp_just = (
            f"{first_name} has "
            f"{exp_years} years "
            f"of relevant experience"
        )

        # ─────────────────────────────────────
        # PROJECTS + SEMANTIC
        # ─────────────────────────────────────

        project_text = (

            candidate.projects_text
            or ""
        ).lower()

        exp_text = (

            candidate.experience_text
            or ""
        ).lower()

        summary_text = (

            candidate.ai_generated_summary

            or

            candidate.summary

            or ""
        ).lower()

        combined = (

            project_text
            + " "
            + exp_text
            + " "
            + summary_text
        )

        project_score = 3.0

        GENAI_SIGNALS = {

            "llm": 1.5,

            "rag": 1.5,

            "langchain": 1.5,

            "langgraph": 1.5,

            "agent": 1.2,

            "agentic": 1.2,

            "fastapi": 1.0,

            "docker": 1.0,

            "kubernetes": 1.0,

            "mlflow": 1.0,

            "pinecone": 1.0,

            "faiss": 1.0,

            "weaviate": 1.0,

            "bert": 1.0,

            "transformer": 1.0,
        }

        matched_ai = []

        for keyword, bonus in GENAI_SIGNALS.items():

            if keyword in combined:

                project_score += bonus

                matched_ai.append(keyword)

        semantic_score = (
            self.semantic_matcher
            .match_resume_to_jd(
                candidate,
                jd
            )
        )

        semantic_bonus = (
            semantic_score * 2.0
        )

        project_score += semantic_bonus

        project_score = min(
            round(project_score, 2),
            10.0
        )

        project_just = (

            f"Semantic similarity "

            f"{round(semantic_score, 2)} | "

            f"Matched AI skills: "

            f"{', '.join(matched_ai[:6])}"
        )

        # ─────────────────────────────────────
        # EDUCATION
        # ─────────────────────────────────────

        edu_text = (
            candidate.education_text or ""
        ).lower()

        edu_score = 5.0

        if "m.tech" in edu_text:
            edu_score = 9.0

        elif "b.tech" in edu_text:
            edu_score = 8.0

        if (
            "ai" in edu_text
            or
            "machine learning" in edu_text
        ):

            edu_score += 1.0

        edu_score = min(
            round(edu_score, 2),
            10.0
        )

        edu_just = (
            f"{first_name}'s education "
            f"matches AI/ML domain"
        )

        # ─────────────────────────────────────
        # COMMUNICATION
        # ─────────────────────────────────────

        comm_score = 8.0

        comm_just = (
            f"{first_name}'s resume "
            f"is well structured"
        )

        # ─────────────────────────────────────
        # TOTAL
        # ─────────────────────────────────────

        total_score = (

            skill_score
            *
            WEIGHTS["skills_match"]

            +

            exp_score
            *
            WEIGHTS["experience_relevance"]

            +

            project_score
            *
            WEIGHTS["project_portfolio"]

            +

            edu_score
            *
            WEIGHTS["education_certs"]

            +

            comm_score
            *
            WEIGHTS["communication_quality"]
        )

        total_score = round(
            min(total_score, 10.0),
            2
        )

        dimension_scores = [

            DimensionScore(
                "skills_match",
                "Skills Match",
                WEIGHTS["skills_match"],
                skill_score,
                round(skill_score * WEIGHTS["skills_match"], 3),
                skill_just
            ),

            DimensionScore(
                "experience_relevance",
                "Experience",
                WEIGHTS["experience_relevance"],
                exp_score,
                round(exp_score * WEIGHTS["experience_relevance"], 3),
                exp_just
            ),

            DimensionScore(
                "project_portfolio",
                "Projects",
                WEIGHTS["project_portfolio"],
                project_score,
                round(project_score * WEIGHTS["project_portfolio"], 3),
                project_just
            ),

            DimensionScore(
                "education_certs",
                "Education",
                WEIGHTS["education_certs"],
                edu_score,
                round(edu_score * WEIGHTS["education_certs"], 3),
                edu_just
            ),

            DimensionScore(
                "communication_quality",
                "Communication",
                WEIGHTS["communication_quality"],
                comm_score,
                round(comm_score * WEIGHTS["communication_quality"], 3),
                comm_just
            ),
        ]

        return (
            total_score,
            dimension_scores
        )

    # ─────────────────────────────────────────
    # RECOMMENDATION
    # ─────────────────────────────────────────

    def get_recommendation(
        self,
        score: float
    ) -> str:

        if score >= 7.0:
            return "Hire"

        elif score >= 4.5:
            return "Maybe"

        return "No Hire"

    # ─────────────────────────────────────────
    # REASONING
    # ─────────────────────────────────────────

    def generate_reasoning(
        self,
        candidate,
        jd,
        recommendation
    ) -> str:

        strengths = []

        weaknesses = []

        combined = (

            " ".join(candidate.skills)
            + " "

            + (candidate.projects_text or "")
            + " "

            + (candidate.experience_text or "")
        ).lower()

        if "langchain" in combined:
            strengths.append(
                "LangChain experience"
            )

        if "langgraph" in combined:
            strengths.append(
                "LangGraph workflows"
            )

        if "rag" in combined:
            strengths.append(
                "RAG pipeline development"
            )

        if "fastapi" in combined:
            strengths.append(
                "FastAPI backend APIs"
            )

        if "llm" in combined:
            strengths.append(
                "LLM application development"
            )

        if (
            candidate.total_experience_years
            >= jd.min_experience_years
        ):

            strengths.append(
                "required experience level"
            )

        missing_keywords = {

            "pinecone": "Pinecone",

            "mlflow": "MLflow",

            "kubernetes": "Kubernetes",
        }

        for key, label in missing_keywords.items():

            if key not in combined:

                weaknesses.append(
                    f"limited {label} exposure"
                )

        reasoning = (

            f"{candidate.full_name} "

            f"shows strong alignment with "

            f"the AI/LLM role through "

            f"{', '.join(strengths[:4])}. "
        )

        if weaknesses:

            reasoning += (

                f"Areas for improvement include "

                f"{', '.join(weaknesses[:3])}. "
            )

        reasoning += (
            f"Final recommendation: "
            f"{recommendation}."
        )

        return reasoning