# agents/amarstock_scraper.py
import requests
import pandas as pd
from io import StringIO
from crewai import Agent
import re
from typing import ClassVar, Optional, List

class AmarStockScraperAgent(Agent):
    role: ClassVar[str] = "Scraper"
    goal: ClassVar[str] = "Download historical stock CSV from AmarStock and parse X/Y axis."
    backstory: ClassVar[str] = "Automate CSV download to get dates and closing prices."

    def run(self, symbol: str, x_axis_dates: Optional[List[str]] = None):
        try:
            base_url = f"https://www.amarstock.com/company/{symbol}"
            headers = {"User-Agent": "Mozilla/5.0"}

            # Step 1: Get company page
            resp = requests.get(base_url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return {"error": f"Company page not found: {resp.status_code}", "axis": []}

            # Step 2: Find CSV link (simple regex)
            match = re.search(r'href="([^"]+\.csv)"', resp.text)
            if not match:
                return {"error": "CSV link not found on company page.", "axis": []}

            csv_url = match.group(1)
            if not csv_url.startswith("http"):
                csv_url = "https://www.amarstock.com" + csv_url

            # Step 3: Download CSV
            csv_resp = requests.get(csv_url, headers=headers, timeout=10)
            if csv_resp.status_code != 200:
                return {"error": f"CSV download failed: {csv_resp.status_code}", "axis": []}

            df = pd.read_csv(StringIO(csv_resp.text))
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
            df['Close'] = pd.to_numeric(df['Close'], errors='coerce')

            if x_axis_dates:
                df = df[df['Date'].isin(x_axis_dates)]

            x_vals = df['Date'].tolist()
            y_vals = df['Close'].tolist()

            return {"axis": [{"x": x_vals, "y": y_vals, "name": "Price"}],
                    "source_url": csv_url}

        except Exception as e:
            return {"error": f"CSV scraping failed: {e}", "axis": []}