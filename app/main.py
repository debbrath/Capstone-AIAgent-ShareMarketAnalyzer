# app/main.py
from fastapi import FastAPI, UploadFile, Form
from pydantic import BaseModel
import uvicorn
from agents.agents_pipeline import crew
import numpy as np
from typing import Optional, List
import pandas as pd


app = FastAPI(title="FirstAPI - Prediction Agent")

# -----------------------
# Request Model
# -----------------------
class PredictRequest(BaseModel):
    source_url: Optional[str] = None
    symbol: Optional[str] = None
    horizon_days: int = 30
    x_axis_dates: Optional[List[str]] = None 

# -----------------------
# Ingest Endpoint
# -----------------------
@app.post("/ingest")
async def ingest(url: Optional[str] = Form(None), file: Optional[UploadFile] = None):
    """
    Ingest a company URL or an uploaded CSV/Excel.
    """
    return {"status": "ingest started", "url": url, "file": getattr(file, "filename", None)}
# -----------------------
# Predict Endpoint
# -----------------------
@app.post("/predict")
async def predict(req: PredictRequest):
    try:
        # 1️⃣ Scrape data (ScraperAgent)
        docs = crew.agents[0].run(req.source_url, x_axis_dates=req.x_axis_dates)
        if docs.get("error"):
            return {"error": f"Scraping failed: {docs['error']}"}

        # 2️⃣ Research (placeholder)
        crew.agents[1].run(req.source_url)

        # 3️⃣ Extract features (FeatureAgent)
        features = crew.agents[2].run(docs).get("features", {})

        # 4️⃣ Predict using ModelAgent
        prediction = crew.agents[3].run(features)

        # 5️⃣ Build axis_data with slope/mean/std/growth
        axis_features = []
        if docs.get("axis"):
            for i, ax in enumerate(docs["axis"]):
                x_vals = ax.get("x", [])
                y_vals = ax.get("y", [])
                slope = features.get(f"axis_{i}_slope", 0.0)
                y_mean = features.get(f"axis_{i}_y_mean", None)
                y_std = features.get(f"axis_{i}_y_std", None)
                growth = features.get(f"axis_{i}_growth_pct", None)

                axis_features.append({
                    "axis_index": i,
                    "name": ax.get("name", f"series_{i}"),
                    "x_values": x_vals,
                    "y_values": y_vals,
                    "slope": slope,
                    "y_mean": y_mean,
                    "y_std": y_std,
                    "growth_pct": growth
                })

        # 6️⃣ Build final response        
        result = {
            "symbol": req.symbol,
            "lower_limit": prediction.get("lower"),
            "upper_limit": prediction.get("upper"),
            "confidence": 0.78,
            "explanation": f"Features used: {prediction.get('meta', {}).get('features_used', {})}",
            "sources": [req.source_url],
            "axis_data": axis_features
        }

        return result

    except Exception as e:
        return {"error": str(e)}

# ----------------------- Service Status -----------------------
@app.get("/status")
async def status():
    return {"service": "running", "model_last_trained": None}

# ----------------------- Run API -----------------------
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)