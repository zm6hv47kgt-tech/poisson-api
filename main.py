# FastAPI Poisson Odds API – v1
# Author: AUB
# Description: Mic API care calculează probabilități și cote corecte pentru meciuri

from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from math import exp
from typing import Optional, Dict, List
import os

# ----------------------------------------------------
# Config
# ----------------------------------------------------
raw_keys = os.environ.get("API_KEYS", "")
API_KEYS = {k.strip() for k in raw_keys.split(",") if k.strip()}

def require_api_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True

app = FastAPI(title="Poisson Odds API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# Models
# ----------------------------------------------------
class PredictRequest(BaseModel):
    home: str
    away: str
    maxGoals: int = 7

class ScoreProb(BaseModel):
    h: int
    a: int
    p: float

# ----------------------------------------------------
# Helpers
# ----------------------------------------------------
def factorial(n: int) -> int:
    r = 1
    for i in range(2, n + 1):
        r *= i
    return r

def pois(k: int, lam: float) -> float:
    return exp(-lam) * lam**k / factorial(k)

def to_odds(p: float) -> float:
    return round(1 / max(1e-12, p), 4)

def poisson_calc(lamH: float, lamA: float, maxGoals: int = 7):
    pH = pD = pA = pOver = pBTTS = 0
    grid = []
    for h in range(maxGoals + 1):
        for a in range(maxGoals + 1):
            p = pois(h, lamH) * pois(a, lamA)
            grid.append({"h": h, "a": a, "p": p})
            if h > a: pH += p
            elif h == a: pD += p
            else: pA += p
            if h + a >= 3: pOver += p
            if h > 0 and a > 0: pBTTS += p
    s = pH + pD + pA
    return {
        "home": pH/s, "draw": pD/s, "away": pA/s,
        "over25": pOver, "btts": pBTTS,
        "scores": sorted(grid, key=lambda x: x["p"], reverse=True)[:10]
    }

# ----------------------------------------------------
# API Routes
# ----------------------------------------------------
@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/v1/predict")
def predict(req: PredictRequest, _: bool = Depends(require_api_key)):
    # exemplu simplu de model: ambele echipe au forță medie
    mu = float(os.environ.get("MU_DEFAULT", 1.35))
    home_adv = float(os.environ.get("HOME_ADV", 1.10))

    lamH = mu * home_adv
    lamA = mu

    res = poisson_calc(lamH, lamA, req.maxGoals)
    return {
        "home": req.home,
        "away": req.away,
        "probabilities": {
            "home": round(res["home"], 4),
            "draw": round(res["draw"], 4),
            "away": round(res["away"], 4)
        },
        "fair_odds": {
            "home": to_odds(res["home"]),
            "draw": to_odds(res["draw"]),
            "away": to_odds(res["away"])
        },
        "extra": {
            "over25": round(res["over25"], 4),
            "btts_yes": round(res["btts"], 4)
        },
        "top_scores": res["scores"][:10]
    }
