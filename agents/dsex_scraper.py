# agents/dsex_scraper.py
import yfinance as yf
import pandas as pd
from crewai import Agent
from typing import ClassVar, Optional, List

class DSEXScraperAgent(Agent):
    role: ClassVar[str] = "Scraper"
    goal: ClassVar[str] = "Download historical DSEX index data and parse X/Y axis."
    backstory: ClassVar[str] = "Automate DSEX historical data download for analysis."

    def run(self, start_date: str = "2013-01-01", end_date: str = "2025-10-20", x_axis_dates: Optional[List[str]] = None):
        try:
            ticker_symbol = "^DSEX"
            data = yf.download(ticker_symbol, start=start_date, end=end_date)

            data.reset_index(inplace=True)
            data['Date'] = pd.to_datetime(data['Date']).dt.strftime('%Y-%m-%d')

            if x_axis_dates:
                data = data[data['Date'].isin(x_axis_dates)]

            x_vals = data['Date'].tolist()
            y_vals = data['Close'].tolist()

            # Save CSV
            data.to_csv("DSEX_historical_data.csv", index=False)

            return {"axis": [{"x": x_vals, "y": y_vals, "name": "DSEX Close"}],
                    "source": "Yahoo Finance via yfinance"}

        except Exception as e:
            return {"error": f"DSEX data download failed: {e}", "axis": []}

# Example usage
if __name__ == "__main__":
    scraper = DSEXScraperAgent()
    result = scraper.run(x_axis_dates=["2025-10-18", "2025-10-19", "2025-10-20"])
    print(result)