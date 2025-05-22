from fastapi import FastAPI, Query
from typing import List, Dict
import httpx
from datetime import datetime, timedelta
from typing import List
import numpy as np

app = FastAPI()

AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiZXhwIjoxNzQ3ODkwMjM2LCJpYXQiOjE3NDc4ODk5MzYsImlzcyI6IkFmZm9yZG1lZCIsImp0aSI6ImE0OGRiYjRkLTMyMWUtNGY1OS1iNWNmLTdiYjMwOTJhNmVlZiIsInN1YiI6IjIyMDAwMzE3OTdjc2VoQGdtYWlsLmNvbSJ9LCJlbWFpbCI6IjIyMDAwMzE3OTdjc2VoQGdtYWlsLmNvbSIsIm5hbWUiOiJhbGxhIGthdnlhIiwicm9sbE5vIjoiMjIwMDAzMTc5NyIsImFjY2Vzc0NvZGUiOiJiZVRKakoiLCJjbGllbnRJRCI6ImE0OGRiYjRkLTMyMWUtNGY1OS1iNWNmLTdiYjMwOTJhNmVlZiIsImNsaWVudFNlY3JldCI6InFrcXVyZEZVYlZ2YnVScEQifQ.m--JbyKbuRLImXOU0almorJLtdG_tZl5zhEngNNnCTU"
BASE_URL = "http://20.244.56.144/evaluation-service"

HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

@app.get("/stocks/{ticker}")
async def get_stock_data(ticker: str, minutes: int = 10, aggregation: str = "average"):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/stocks/{ticker}", headers=HEADERS)
        if response.status_code != 200:
            return {"error": "Unable to fetch data from stock API"}

        price_history = response.json()
        filtered_data = filter_by_minutes(price_history, minutes)
        avg_price = calculate_average(filtered_data)

        return {
            "averageStockPrice": round(avg_price, 6),
            "priceHistory": filtered_data
        }

@app.get("/stockcorrelation")
async def get_stock_correlation(
    minutes: int = Query(...),
    ticker: List[str] = Query(...)
):
    if len(ticker) != 2:
        return {"error": "Exactly two tickers must be provided"}

    async with httpx.AsyncClient() as client:
        data = {}
        for t in ticker:
            resp = await client.get(f"{BASE_URL}/stocks/{t}", headers=HEADERS)
            if resp.status_code != 200:
                return {"error": f"Error fetching data for {t}"}
            all_data = resp.json()
            filtered = filter_by_minutes(all_data, minutes)
            avg = calculate_average(filtered)
            data[t] = {
                "priceHistory": filtered,
                "averagePrice": round(avg, 6)
            }

        correlation = calculate_correlation(
            data[ticker[0]]["priceHistory"],
            data[ticker[1]]["priceHistory"]
        )

        return {
            "correlation": round(correlation, 4),
            "stocks": data
        }

def filter_by_minutes(data, minutes):
    now = datetime.utcnow()
    threshold = now - timedelta(minutes=minutes)
    return [d for d in data if datetime.fromisoformat(d['lastUpdatedAt'].replace("Z", "+00:00")) >= threshold]

def calculate_average(data):
    if not data:
        return 0
    return sum(d["price"] for d in data) / len(data)

def calculate_correlation(data1, data2):
    prices1 = [d["price"] for d in data1]
    prices2 = [d["price"] for d in data2]

    min_len = min(len(prices1), len(prices2))
    if min_len < 2:
        return 0

    return float(np.corrcoef(prices1[:min_len], prices2[:min_len])[0, 1])
