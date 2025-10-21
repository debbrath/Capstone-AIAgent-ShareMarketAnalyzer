# agents/FeatureAgent.py
import pandas as pd
import numpy as np
from crewai import Agent
from typing import ClassVar, Optional, List, Dict, Any


class FeatureAgent(Agent):
    role: ClassVar[str] = "Feature Engineer"
    goal: ClassVar[str] = "Convert scraped Biniyog chart data into robust numeric features"
    backstory: ClassVar[str] = "Compute slope, mean, std, growth, and trend per series for ML prediction"
    def run(self, docs):
        features = {}

        try:
            # ---------------- Process each axis (chart series) ----------------
            if docs.get("axis"):
                for i, ax in enumerate(docs["axis"]):
                    x_raw = ax.get("x", [])
                    y_raw = ax.get("y", [])
                    series_name = ax.get("name", f"series_{i}")

                    if not x_raw or not y_raw or len(x_raw) != len(y_raw):
                        continue

                    # Parse dates
                    x_dates = pd.to_datetime(x_raw, errors='coerce')
                    mask = x_dates.notna()
                    x_dates = x_dates[mask]
                    y = np.array([float(v) for v, m in zip(y_raw, mask) if m])

                    if len(y) < 1:
                        continue

                    # Days since first point
                    days = (x_dates - x_dates.min()).dt.days.values
                    if len(days) < 2:
                        days = np.arange(len(y))

                    # ---------------- Compute features ----------------
                    slope = float(np.polyfit(np.arange(len(y)), y, 1)[0]) if len(y) > 1 else 0.0
                    y_mean = float(np.mean(y))
                    y_std = float(np.std(y))
                    growth_pct = float((y[-1] - y[0]) / y[0] * 100) if y[0] != 0 else 0.0
                    max_val = float(np.max(y))
                    min_val = float(np.min(y))
                    last_val = float(y[-1])

                    # Prefix features with series index and name
                    prefix = f"axis_{i}_{series_name.lower().replace(' ', '_')}"

                    features[f"{prefix}_slope"] = slope
                    features[f"{prefix}_mean"] = y_mean
                    features[f"{prefix}_std"] = y_std
                    features[f"{prefix}_growth_pct"] = growth_pct
                    features[f"{prefix}_max"] = max_val
                    features[f"{prefix}_min"] = min_val
                    features[f"{prefix}_last"] = last_val

            # ---------------- Fallback if no axis data ----------------
            if not features:
                features["example_feature"] = 1

        except Exception as e:
            features["error"] = f"Feature extraction failed: {e}"
            if not features.get("example_feature"):
                features["example_feature"] = 1

        return {"features": features}