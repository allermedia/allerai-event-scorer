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

            # if multiple versions exist, take the last one (latest)
            if isinstance(domain_config, dict) and any(isinstance(v, dict) for v in domain_config.values()):
                latest_version = list(domain_config.keys())[-1]
                weights = domain_config[latest_version]
            else:
                weights = domain_config

            weights = {k: v for k, v in weights.items() if k in row}

            # normalize weights
            total_weight = sum(weights.values())
            if self.normalize and total_weight > 0:
                weights = {k: v / total_weight for k, v in weights.items()}

            score = sum(row.get(feature, 0.0) * weight for feature, weight in weights.items())

            results.append({
                "id": row["id"],
                "site_domain": row["site_domain"],
                "score": score
            })

        return pd.DataFrame(results)
