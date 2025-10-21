from crewai import Agent
import pandas as pd
from models.utils import load_model

import numpy as np
import joblib
from crewai import Agent
import os
from typing import ClassVar, Optional, List, Dict, Any


class ModelAgent(Agent):
    role: ClassVar[str] = "Predictor"
    goal: ClassVar[str] = "Predict upper and lower limits using quantile regression or fallback heuristic"
    backstory: ClassVar[str] = "Applies trained quantile models to feature data; uses fallback if unavailable"

    def run(self, features: dict):
        result = {}
        meta_info = {"features_used": features}

        try:
            # ------------------------
            # 1️⃣ Prepare feature DataFrame
            # ------------------------
            if not features or not isinstance(features, dict):
                raise ValueError("Invalid feature input")

            X = pd.DataFrame([features])

            # ------------------------
            # 2️⃣ Load models dynamically
            # ------------------------
            upper_path = "models/quantile_q90.pkl"
            lower_path = "models/quantile_q10.pkl"

            if not os.path.exists(upper_path) or not os.path.exists(lower_path):
                raise FileNotFoundError("Quantile models not found")

            model_upper = joblib.load(upper_path)
            model_lower = joblib.load(lower_path)

            # ------------------------
            # 3️⃣ Predict upper/lower limits
            # ------------------------
            upper = float(model_upper.predict(X)[0])
            lower = float(model_lower.predict(X)[0])

            result = {
                "upper": round(upper, 2),
                "lower": round(lower, 2),
                "meta": meta_info
            }

        except Exception as e:
            # ------------------------
            # 4️⃣ Fallback logic (simple heuristic)
            # ------------------------
            profit = features.get("last_profit", 100.0)
            revenue = features.get("last_revenue", 1000.0)

            # Use trend/growth features if available
            slope = features.get("axis_0_slope_per_day", 0.0)
            growth = features.get("axis_0_growth_pct", 0.0)

            ratio = profit / revenue if revenue else 0.1
            base = (revenue * ratio * 0.1) + slope + (growth / 100)

            upper = base * 1.2
            lower = base * 0.8

            result = {
                "upper": round(upper, 2),
                "lower": round(lower, 2),
                "meta": {**meta_info, "fallback_reason": str(e)}
            }

        return result