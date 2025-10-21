# agents/agents_pipeline.py
import requests
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
import numpy as np
import joblib
from crewai import Crew, Agent
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json, re, pandas as pd, time, numpy as np
import ast
from typing import ClassVar, Optional, List, Dict, Any



# -----------------------
# 1️⃣ Scraper Agent
# -----------------------
class ScraperAgent(Agent):
    role: ClassVar[str] = "Scraper"
    goal: ClassVar[str] = "Scrape AmarStock historical stock data."
    backstory: ClassVar[str] = "Extract X/Y axis (date/closing price) from AmarStock company pages."

    def run(self, url, x_axis_dates=None):
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            driver = webdriver.Chrome(service=Service(), options=options)
            driver.get(url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            html = driver.page_source
            driver.quit()

            # Extract JS arrays like: window.chartData = [{date:'2025-10-23', close:210.0}, ...]
            pattern = r"window\.chartData\s*=\s*(\[[^\]]+\])"
            match = re.search(pattern, html)
            if not match:
                return {"error": "No chartData found in page", "axis": []}

            data_js = match.group(1)
            # Replace JS object syntax to valid Python
            data_py = data_js.replace("null", "None").replace("true", "True").replace("false", "False")
            data_list = eval(data_py)  # safe because we control the content

            # Parse dates and closing prices
            x_vals, y_vals = [], []
            for item in data_list:
                date = item.get('date')
                close = item.get('close')
                if date and close:
                    x_vals.append(date)
                    y_vals.append(float(close))

            # Filter by requested dates
            if x_axis_dates:
                x_filtered, y_filtered = [], []
                for d, v in zip(x_vals, y_vals):
                    if d in x_axis_dates:
                        x_filtered.append(d)
                        y_filtered.append(v)
                x_vals, y_vals = x_filtered, y_filtered

            return {"axis": [{"x": x_vals, "y": y_vals, "name": "Price"}], "source_url": url}

        except Exception as e:
            return {"error": f"Scraping failed: {e}", "axis": []}
        
# -----------------------
# 2️⃣ Research Agent (placeholder)
# -----------------------
class ResearchAgent(Agent):
    role: ClassVar[str] = "Researcher"
    goal: ClassVar[str] = "Retrieve historical articles or reports for context"
    backstory: ClassVar[str] = "Responsible for finding external information for predictions"

    def run(self, query):
        return {"articles": []}  # placeholder for RAG

# -----------------------
# 3️⃣ Feature Agent
# -----------------------
class FeatureAgent(Agent):
    role: str = "Feature Engineer"
    goal: str = "Convert raw scraped data into numeric features for ML"
    backstory: str = "Extract numeric features from tables, text, and chart axes"

    def run(self, docs):
        features = {}

        try:
            # ------------------------
            # Extract numeric features from first table
            # ------------------------
            if docs.get("tables"):
                first_table = docs["tables"][0]
                if len(first_table) > 1:
                    df = pd.DataFrame(first_table[1:], columns=first_table[0])
                    numeric_cols = []
                    for col in df.columns:
                        try:
                            df[col] = df[col].str.replace(",", "").replace("-", "0").astype(float)
                            numeric_cols.append(col)
                        except Exception:
                            continue
                    for col in numeric_cols:
                        features[f"last_{col.lower().replace(' ', '_')}"] = df[col].iloc[-1]

            # ------------------------
            # Extract features from X/Y axis
            # ------------------------
            if docs.get("axis"):
                for i, ax in enumerate(docs["axis"]):
                    try:
                        x_numeric = np.arange(len(ax["x"]))  # use indices for slope
                        y = np.array([float(v) for v in ax["y"]])
                        slope = float(np.polyfit(x_numeric, y, 1)[0])
                        y_mean = float(np.mean(y))
                        features[f"axis_{i}_slope"] = slope
                        features[f"axis_{i}_y_mean"] = y_mean
                    except Exception:
                        continue

            # Fallback dummy feature
            if not features:
                features["example_feature"] = 1

        except Exception as e:
            features["error"] = f"Feature extraction failed: {e}"

        return {"features": features}

# -----------------------
# 4️⃣ Model Agent
# -----------------------
class ModelAgent(Agent):
    role: str = "Predictor"
    goal: str = "Predict upper and lower limits using features"
    backstory: str = "Apply quantile models to compute predictions"

    def run(self, features):
        try:
            X = pd.DataFrame([features])
            model_upper = joblib.load("models/quantile_q90.pkl")
            model_lower = joblib.load("models/quantile_q10.pkl")
            upper = model_upper.predict(X)[0]
            lower = model_lower.predict(X)[0]
            return {"upper": upper, "lower": lower, "meta": {"features_used": features}}
        except Exception as e:
            # fallback simple logic
            profit = features.get("last_profit", 100)
            revenue = features.get("last_revenue", 1000)
            ratio = profit / revenue if revenue else 0.1
            base = revenue * ratio * 0.1
            upper = base * 1.2
            lower = base * 0.8
            return {"upper": round(upper, 2), "lower": round(lower, 2),
                    "meta": {"features_used": features, "error": str(e)}}

# -----------------------
# 5️⃣ Compose Crew
# -----------------------
crew = Crew(
    name="rupalilife_predict_crew",
    agents=[ScraperAgent(), ResearchAgent(), FeatureAgent(), ModelAgent()]
)