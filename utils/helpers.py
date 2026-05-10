"""
utils/helpers.py
----------------
Report Generation: JSON, TXT, HTML
"""

import json
from datetime import datetime
from pathlib import Path

from scoring.scorer import ScoreResult
from parsers.jd_parser import ParsedJD


class ReportGenerator:

    def __init__(self, output_dir: str = "data/reports"):

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def generate_all(
        self,
        ranked: list[ScoreResult],
        jd: ParsedJD
    ) -> dict[str, str]:

        ts = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        base = f"shortlist_{ts}"

        return {

            "json":
                self._json(
                    ranked,
                    jd,
                    base
                ),

            "txt":
                self._txt(
                    ranked,
                    jd,
                    base
                ),

            "html":
                self._html(
                    ranked,
                    jd,
                    base
                ),
        }

    def _json(self, ranked, jd, base) -> str:

        payload = {

            "generated_at":
                datetime.now().isoformat(),

            "job": {

                "title":
                    jd.title,

                "company":
                    jd.company,

                "domain":
                    jd.industry_domain,
            },

            "summary": {

                "total":
                    len(ranked),

                "hire":
                    sum(
                        1 for c in ranked
                        if c.recommendation == "Hire"
                    ),

                "maybe":
                    sum(
                        1 for c in ranked
                        if c.recommendation == "Maybe"
                    ),

                "no_hire":
                    sum(
                        1 for c in ranked
                        if c.recommendation == "No Hire"
                    ),
            },

            "shortlist": [

                {

                    "rank":
                        i + 1,

                    "name":
                        c.candidate_name,

                    "role":
                        c.current_role,

                    "total_score":
                        c.total_score,

                    "percentage":
                        c.percentage,

                    "recommendation":
                        c.recommendation,

                    "summary":
                        c.ai_summary,

                    "reasoning":
                        c.final_reasoning,

                    "dimensions": [

                        {

                            "label":
                                ds.label,

                            "weight":
                                f"{int(ds.weight * 100)}%",

                            "score":
                                ds.raw_score,

                            "weighted":
                                ds.weighted_score,

                            "justification":
                                ds.justification,

                        }

                        for ds in c.dimension_scores
                    ],

                    "override_log":
                        c.override_log,
                }

                for i, c in enumerate(ranked)
            ],
        }

        path = self.output_dir / f"{base}.json"

        path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8"
        )

        return str(path)

    def _txt(self, ranked, jd, base) -> str:

        lines = []

        sep = "=" * 65

        lines += [

            sep,

            "  HR SHORTLISTING REPORT",

            f"  {datetime.now().strftime('%d %b %Y, %H:%M')}",

            sep,

            f"  Role    : {jd.title} @ {jd.company}",

            f"  Domain  : {jd.industry_domain}",

            f"  Exp Req : "
            f"{jd.min_experience_years}-"
            f"{jd.max_experience_years} yr | "
            f"{jd.seniority_level}",

            sep,

            f"  Total: {len(ranked)}  "
            f"Hire: {sum(1 for c in ranked if c.recommendation=='Hire')}  "
            f"Maybe: {sum(1 for c in ranked if c.recommendation=='Maybe')}  "
            f"No Hire: {sum(1 for c in ranked if c.recommendation=='No Hire')}",

            sep,
            "",
        ]

        for i, c in enumerate(ranked, 1):

            badge = {

                "Hire": "HIRE",

                "Maybe": "MAYBE",

                "No Hire": "NO HIRE"

            }[c.recommendation]

            lines += [

                f"  #{i}  {c.candidate_name}",

                f"      {c.current_role}",

                f"      Score: "
                f"{c.total_score:.2f}/10  "
                f"({c.percentage}%)   {badge}",

                f"      {c.ai_summary}",

                "",

                f"      {'Dimension':<26} "
                f"{'Wt':>4}  "
                f"{'Score':>5}  "
                f"Justification",

                f"      {'-'*26} "
                f"{'--':>4}  "
                f"{'-----':>5}  "
                f"{'-'*30}",
            ]

            for ds in c.dimension_scores:

                lines.append(

                    f"      {ds.label:<26} "
                    f"{int(ds.weight*100):>3}%  "
                    f"{ds.raw_score:>5.1f}  "
                    f"{ds.justification}"
                )

            lines += [

                f"      {'TOTAL':<26}       "
                f"{c.total_score:>5.2f}",

                "",

                "  " + "-" * 63,

                ""
            ]

        path = self.output_dir / f"{base}.txt"

        path.write_text(
            "\n".join(lines),
            encoding="utf-8"
        )

        return str(path)

    def _html(self, ranked, jd, base) -> str:

        hire = sum(
            1 for c in ranked
            if c.recommendation == "Hire"
        )

        maybe = sum(
            1 for c in ranked
            if c.recommendation == "Maybe"
        )

        no_hire = sum(
            1 for c in ranked
            if c.recommendation == "No Hire"
        )

        cards = ""

        for i, c in enumerate(ranked, 1):

            cls = {

                "Hire": "hire",

                "Maybe": "maybe",

                "No Hire": "nohire"

            }[c.recommendation]

            badge = {

                "Hire": "Hire",

                "Maybe": "Maybe",

                "No Hire": "No Hire"

            }[c.recommendation]

            dims = ""

            for ds in c.dimension_scores:

                pct = ds.raw_score * 10

                color = (
                    "#1D9E75"
                    if ds.raw_score >= 7.5
                    else "#BA7517"
                    if ds.raw_score >= 5
                    else "#E24B4A"
                )

                dims += f"""
                <div class="dim">
                  <span class="dl">{ds.label}</span>
                  <div class="bw">
                    <div class="b"
                      style="width:{pct}%;
                      background:{color}">
                    </div>
                  </div>
                  <span class="ds">{ds.raw_score:.1f}</span>
                  <span class="dw">{int(ds.weight*100)}%</span>
                  <span class="dj">{ds.justification}</span>
                </div>
                """

            cards += f"""
            <div class="card {cls}">
              <div class="ct">

                <div class="rk">#{i}</div>

                <div class="ci">
                  <div class="cn">{c.candidate_name}</div>
                  <div class="cr">{c.current_role}</div>
                </div>

                <div class="sb">
                  <div class="ts">
                    {c.total_score:.2f}<span>/10</span>
                  </div>

                  <div class="bd {cls}">
                    {badge}
                  </div>
                </div>

              </div>

              <p class="sm">
                {c.ai_summary}
              </p>

              <div class="dh">
                <span>Dimension</span>
                <span></span>
                <span>Score</span>
                <span>Wt</span>
                <span>Justification</span>
              </div>

              {dims}

            </div>
            """

        html = f"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<title>
HR Shortlist - {jd.title}
</title>

<style>

body {{
    font-family: Arial;
    background: #f5f5f5;
    padding: 30px;
}}

.card {{
    background: white;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 10px;
}}

.hire {{
    border-left: 5px solid green;
}}

.maybe {{
    border-left: 5px solid orange;
}}

.nohire {{
    border-left: 5px solid red;
}}

</style>

</head>

<body>

<h1>
HR Shortlisting Report
</h1>

<h2>
{jd.title}
</h2>

<p>
{jd.company}
</p>

{cards}

</body>
</html>
"""

        path = self.output_dir / f"{base}.html"

        path.write_text(
            html,
            encoding="utf-8"
        )

        return str(path)