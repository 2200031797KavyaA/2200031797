from fastapi import FastAPI, HTTPException
from collections import deque
from typing import List
import httpx
import time

app = FastAPI()

WINDOW_SIZE = 10
THIRD_PARTY_BASE_URL = "http://localhost:9876/numbers/e"
TIMEOUT_MS = 0.5

number_window = deque(maxlen=WINDOW_SIZE)

AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiZXhwIjoxNzQ3ODkwMjM2LCJpYXQiOjE3NDc4ODk5MzYsImlzcyI6IkFmZm9yZG1lZCIsImp0aSI6ImE0OGRiYjRkLTMyMWUtNGY1OS1iNWNmLTdiYjMwOTJhNmVlZiIsInN1YiI6IjIyMDAwMzE3OTdjc2VoQGdtYWlsLmNvbSJ9LCJlbWFpbCI6IjIyMDAwMzE3OTdjc2VoQGdtYWlsLmNvbSIsIm5hbWUiOiJhbGxhIGthdnlhIiwicm9sbE5vIjoiMjIwMDAzMTc5NyIsImFjY2Vzc0NvZGUiOiJiZVRKakoiLCJjbGllbnRJRCI6ImE0OGRiYjRkLTMyMWUtNGY1OS1iNWNmLTdiYjMwOTJhNmVlZiIsImNsaWVudFNlY3JldCI6InFrcXVyZEZVYlZ2YnVScEQifQ.m--JbyKbuRLImXOU0almorJLtdG_tZl5zhEngNNnCTU"

async def fetch_numbers(number_id: str) -> List[int]:
    url_map = {
        "p": "primes",
        "f": "fibo",
        "e": "even",
        "r": "rand"
    }

    if number_id not in url_map:
        return []

    url = f"http://20.244.56.144/evaluation-service/{url_map}"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_MS) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("numbers", [])
    except Exception:
        return []
    return []

@app.get("/numbers/{number_id}")
async def get_numbers(number_id: str):
    if number_id not in ("p", "f", "e", "r"):
        raise HTTPException(status_code=400, detail="Invalid number ID")

    start_time = time.time()
    window_prev_state = list(number_window)

    fetched_numbers = await fetch_numbers(number_id)

    existing_set = set(number_window)
    for num in fetched_numbers:
        if num not in existing_set:
            number_window.append(num)
            existing_set.add(num)

    window_curr_state = list(number_window)

    if len(number_window) == 0:
        avg = 0
    else:
        avg = round(sum(number_window) / len(number_window), 2)

    elapsed = (time.time() - start_time)
    if elapsed > TIMEOUT_MS:
        raise HTTPException(status_code=504, detail="Request timeout")

    return {
        "windowPrevState": window_prev_state,
        "windowCurrState": window_curr_state,
        "numbers": fetched_numbers,
        "avg": avg
    }
