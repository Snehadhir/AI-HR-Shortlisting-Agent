"""
app.py
-------
FINAL Deterministic AI HR Shortlisting Agent
Optimized for CPU + 16GB RAM
"""

import argparse
import sys
import time
import json

from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from llm.llm_engine import LLMEngine

from parsers.jd_parser import JDParser
from parsers.resume_parser import ResumeParser
from parsers.linkedin_parser import LinkedInParser

from scoring.scorer import Scorer
from scoring.ranking import Ranker

from utils.helpers import ReportGenerator


console = Console()


# ─────────────────────────────────────────
# HUMAN OVERRIDE SYSTEM
# ─────────────────────────────────────────

def apply_overrides(results):

    override_file = Path(
        "overrides.json"
    )

    if not override_file.exists():

        return results

    try:

        overrides = json.loads(
            override_file.read_text(
                encoding="utf-8"
            )
        )

    except Exception:

        print(
            "\n⚠ Failed to load overrides.json"
        )

        return results

    for result in results:

        candidate_name = (
            result.candidate_name
        )

        if candidate_name in overrides:

            override = overrides[
                candidate_name
            ]

            old_score = (
                result.total_score
            )

            new_score = float(
                override.get(
                    "new_score",
                    old_score
                )
            )

            reason = override.get(
                "reason",
                "Manual HR override"
            )

            # UPDATE SCORE
            result.total_score = round(
                new_score,
                2
            )

            result.percentage = round(
                new_score * 10,
                2
            )

            # UPDATE RECOMMENDATION

            if new_score >= 7:

                result.recommendation = (
                    "Hire"
                )

            elif new_score >= 4.5:

                result.recommendation = (
                    "Maybe"
                )

            else:

                result.recommendation = (
                    "No Hire"
                )

            # ADD OVERRIDE LOG

            result.override_log.append({

                "old_score": old_score,

                "new_score": new_score,

                "reason": reason
            })

            # APPEND REASONING

            result.final_reasoning += (

                f"\n\n[HR Override Applied] "

                f"Score changed from "

                f"{old_score} to "

                f"{new_score}. "

                f"Reason: {reason}"
            )

            print(

                f"\n✓ HR Override Applied → "

                f"{candidate_name}"
            )

    return results


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():

    start_time = time.time()

    # ─────────────────────────────────────────
    # ARGUMENTS
    # ─────────────────────────────────────────

    parser = argparse.ArgumentParser(

        description=
            "AI HR Shortlisting Agent"
    )

    parser.add_argument(

        "--jd",

        required=True,

        help="Path to JD file"
    )

    parser.add_argument(

        "--resumes",

        default=None,

        help="Resume folder"
    )

    parser.add_argument(

        "--linkedin",

        default=None,

        help="LinkedIn JSON folder"
    )

    parser.add_argument(

        "--output-dir",

        default="data/reports",

        help="Reports output folder"
    )

    args = parser.parse_args()

    # ─────────────────────────────────────────
    # VALIDATION
    # ─────────────────────────────────────────

    if not args.resumes and not args.linkedin:

        console.print(

            "[red]Error:[/red] "

            "Provide resumes or LinkedIn data"
        )

        sys.exit(1)

    # ─────────────────────────────────────────
    # HEADER
    # ─────────────────────────────────────────

    console.print()

    console.print(

        Panel.fit(

            "[bold cyan]AI HR Shortlisting Agent[/bold cyan]\n\n"

            "[white]AI-Powered Resume Screening & Candidate Ranking System[/white]\n\n"

            "[green]Model:[/green] Qwen2.5:1.5b",

            title="System Architecture",

            border_style="cyan",
        )
    )

    console.print()

    # ─────────────────────────────────────────
    # INIT MODEL
    # ─────────────────────────────────────────

    console.print(

        "[bold blue]Initializing Model...[/bold blue]"
    )

    try:

        engine = LLMEngine(

            model="qwen2.5:1.5b"
        )

    except Exception as e:

        console.print(

            f"[red]LLM Initialization Failed:[/red] {e}"
        )

        sys.exit(1)

    console.print(

        "[green]✓[/green] Qwen connected\n"
    )

    # ─────────────────────────────────────────
    # STEP 1 — PARSE JD
    # ─────────────────────────────────────────

    console.print(

        "[bold blue]Step 1/5[/bold blue] "

        "Parsing Job Description..."
    )

    jd_parser = JDParser()

    jd = jd_parser.parse_file(
        args.jd
    )

    console.print(

        f"[green]✓[/green] "

        f"{jd.title}"
    )

    console.print(

        f"[cyan]Company:[/cyan] "

        f"{jd.company}"
    )

    console.print(

        f"[cyan]Required Skills:[/cyan] "

        f"{', '.join(jd.required_skills[:5])}\n"
    )

    # ─────────────────────────────────────────
    # STEP 2 — PARSE CANDIDATES
    # ─────────────────────────────────────────

    console.print(

        "[bold blue]Step 2/5[/bold blue] "

        "Parsing Candidates..."
    )

    candidates = []

    # RESUMES
    if args.resumes:

        resume_parser = ResumeParser()

        candidates.extend(

            resume_parser.parse_batch(
                args.resumes
            )
        )

    # LINKEDIN
    if args.linkedin:

        li_parser = LinkedInParser()

        candidates.extend(

            li_parser.parse_batch(
                args.linkedin
            )
        )

    if not candidates:

        console.print(

            "[red]No candidates loaded.[/red]"
        )

        sys.exit(1)

    console.print(

        f"\n[green]✓[/green] "

        f"Loaded {len(candidates)} "

        f"candidate(s)\n"
    )

    # ─────────────────────────────────────────
    # STEP 3 — SCORING
    # ─────────────────────────────────────────

    console.print(

        "[bold blue]Step 3/5[/bold blue] "

        "Scoring Candidates..."
    )

    scorer = Scorer(engine)

    results = []

    for candidate in candidates:

        result = scorer.score(

            candidate,

            jd
        )

        results.append(result)

        console.print(

            f"[green]✓[/green] "

            f"{result.candidate_name} "

            f"→ "

            f"{result.total_score:.2f}/10 "

            f"({result.recommendation})"
        )

    console.print()

    # ─────────────────────────────────────────
    # APPLY HR OVERRIDES
    # ─────────────────────────────────────────

    results = apply_overrides(results)

    # ─────────────────────────────────────────
    # STEP 4 — RANKING
    # ─────────────────────────────────────────

    console.print(

        "[bold blue]Step 4/5[/bold blue] "

        "Ranking Candidates..."
    )

    ranker = Ranker()

    ranked = ranker.rank(results)

    console.print(

        "[green]✓[/green] Ranking Complete\n"
    )

    # ─────────────────────────────────────────
    # STEP 5 — REPORTS
    # ─────────────────────────────────────────

    console.print(

        "[bold blue]Step 5/5[/bold blue] "

        "Generating Reports..."
    )

    reporter = ReportGenerator(

        output_dir=args.output_dir
    )

    paths = reporter.generate_all(

        ranked,

        jd
    )

    for fmt, path in paths.items():

        console.print(

            f"[green]✓[/green] "

            f"{fmt.upper()} → {path}"
        )

    console.print()

    # ─────────────────────────────────────────
    # FINAL TABLE
    # ─────────────────────────────────────────

    table = Table(

        title=
            f"Ranked Candidates — {jd.title}",

        box=box.ROUNDED,

        show_header=True,

        header_style="bold cyan"
    )

    table.add_column(
        "#",
        style="cyan"
    )

    table.add_column(
        "Candidate"
    )

    table.add_column(
        "Score"
    )

    table.add_column(
        "Decision"
    )

    for i, candidate in enumerate(ranked, 1):

        table.add_row(

            str(i),

            candidate.candidate_name,

            f"{candidate.total_score:.2f}",

            candidate.recommendation
        )

    console.print(table)

    # ─────────────────────────────────────────
    # EXECUTION TIME
    # ─────────────────────────────────────────

    total_time = round(

        time.time() - start_time,

        2
    )

    console.print()

    console.print(

        f"[bold green]Pipeline Complete "

        f"in {total_time}s[/bold green]"
    )


# ─────────────────────────────────────────────
# ENTRY
# ─────────────────────────────────────────────

if __name__ == "__main__":

    main()