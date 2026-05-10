"""
scoring/ranking.py
------------------
Module 4: Candidate Ranker
"""

from statistics import mean


class Ranker:

    def rank(self, candidates):

        return sorted(
            candidates,
            key=lambda c: c.total_score,
            reverse=True
        )

    def get_hire(self, candidates):

        return [
            c for c in candidates
            if c.recommendation == "Hire"
        ]

    def get_maybe(self, candidates):

        return [
            c for c in candidates
            if c.recommendation == "Maybe"
        ]

    def get_no_hire(self, candidates):

        return [
            c for c in candidates
            if c.recommendation == "No Hire"
        ]

    def summary_stats(self, ranked):

        if not ranked:

            return {
                "total": 0,
                "hire": 0,
                "maybe": 0,
                "no_hire": 0,
                "top_score": 0,
                "avg_score": 0,
                "top_candidate": None,
            }

        scores = [
            c.total_score
            for c in ranked
        ]

        return {

            "total":
                len(ranked),

            "hire":
                len(
                    self.get_hire(ranked)
                ),

            "maybe":
                len(
                    self.get_maybe(ranked)
                ),

            "no_hire":
                len(
                    self.get_no_hire(ranked)
                ),

            "top_score":
                round(max(scores), 2),

            "avg_score":
                round(mean(scores), 2),

            "top_candidate":
                ranked[0].candidate_name,
        }