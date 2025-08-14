import pandas as pd
import re

class Tagger:
    def tag_events(self, event_row, nordic_named_entities):
        """Match tags from nordic_named_entities to a single event row."""
        all_matches = []
        full_text = f"{event_row['title']} {event_row['subtitle']} {event_row['bodytext']}".lower()

        for (site, tag_type), group in nordic_named_entities.groupby(["site", "tag_type"]):
            tags = group["tag"].dropna().unique().tolist()
            tag_patterns = [re.compile(rf"\b{re.escape(tag.lower())}\b") for tag in tags]

            matched_tags = [
                tag for tag, pat in zip(tags, tag_patterns)
                if pat.search(full_text)
            ]
            for tag in matched_tags:
                all_matches.append({
                    "id": event_row["id"],
                    "site": site,
                    "tag_type": tag_type,
                    "tag": tag
                })

        return pd.DataFrame(all_matches)

    def tag_relevance(self, event_row, nordic_tag_scores):
        """Tag the event, join scores, and aggregate into per-site results."""
        df_matches = self.tag_events(event_row, nordic_tag_scores)

        if df_matches.empty:
            return pd.DataFrame(columns=["id", "site", "tag_score", "person_tags", "tv_tags"])

        df_matches = df_matches.merge(
            nordic_tag_scores[["site", "tag_type", "tag", "tag_score"]],
            on=["site", "tag_type", "tag"],
            how="left"
        )

        grouped_tags = df_matches.groupby(["id", "site", "tag_type"])["tag"].apply(list).unstack(fill_value=[]).reset_index()
        grouped_tags = grouped_tags.rename(columns={"person": "person_tags", "tv_or_movie": "tv_tags"})

        if "person_tags" not in grouped_tags:
            grouped_tags["person_tags"] = [[] for _ in range(len(grouped_tags))]
        if "tv_tags" not in grouped_tags:
            grouped_tags["tv_tags"] = [[] for _ in range(len(grouped_tags))]

        top_scores = df_matches.groupby(["id", "site"])["tag_score"].max().reset_index()
        result = top_scores.merge(grouped_tags, on=["id", "site"], how="left")

        return result
