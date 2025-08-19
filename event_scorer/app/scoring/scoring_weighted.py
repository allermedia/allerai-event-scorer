import pandas as pd
import yaml
from pathlib import Path

class Scorer:
    def __init__(self, config_path: str = None, normalize: bool = True):
        if config_path is None:
            config_path = Path(__file__).resolve().parent.parent / "models" / "domain_scoring.yaml"
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.normalize = normalize

    def compute_weighted_score(self, df: pd.DataFrame) -> pd.DataFrame:
        results = []

        for _, row in df.iterrows():
            domain_config = self.config.get(row["site_domain"], self.config["default"])

            if isinstance(domain_config, dict) and any(isinstance(v, dict) for v in domain_config.values()):
                latest_version = list(domain_config.keys())[-1]
                weights = domain_config[latest_version]
            else:
                weights = domain_config

            weighted_features = {}
            additive_bonus = 0.0

            for feature, config in weights.items():
                if isinstance(config, dict):
                    f_type = config.get("type", "weighted")
                    f_value = config.get("value", 0.0)
                else:
                    f_type = "weighted"
                    f_value = config

                if f_type == "weighted":
                    weighted_features[feature] = f_value
                elif f_type == "additive":
                    additive_bonus += row.get(feature, 0.0) * f_value

            total_weight = sum(weighted_features.values())
            if self.normalize and total_weight > 0:
                weighted_features = {k: v / total_weight for k, v in weighted_features.items()}

            score = sum(row.get(f, 0.0) * w for f, w in weighted_features.items())

            score = min(score + additive_bonus, 1.0)

            results.append({
                "id": row["id"],
                "site_domain": row["site_domain"],
                "score": score,
                "entities": row["entities"]
            })

        return pd.DataFrame(results)
    