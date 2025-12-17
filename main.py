import yfinance as yf
from datetime import date
import json
import os

OUTPUT_DIR = "output"
HISTORY_DIR = "output/history"

os.makedirs(HISTORY_DIR, exist_ok=True)

SYMBOLS = {
    "gold": "XAUUSD=X",
    "dxy": "DX-Y.NYB",
    "usd_inr": "USDINR=X",
    "us10y": "^TNX",
    "nifty": "^NSEI",
    "india_vix": "^INDIAVIX"
}

def fetch(symbol):
    df = yf.download(symbol, period="7d", interval="1d", progress=False)
    df["pct"] = df["Close"].pct_change() * 100
    return df.dropna()

data = {k: fetch(v) for k, v in SYMBOLS.items()}

global_score = 0
india_score = 0
sentiment_score = 0
notes = []

# Global
if data["dxy"]["pct"].iloc[-1] < -0.3:
    global_score += 1
    notes.append("USD Index weakened → bullish for gold")

if data["us10y"]["pct"].iloc[-1] < -0.5:
    global_score += 1
    notes.append("US bond yields falling → gold positive")

# India
if data["usd_inr"]["pct"].iloc[-1] > 0.2:
    india_score += 1
    notes.append("Rupee weakened → supports Indian gold")

if data["usd_inr"]["Close"].iloc[-1] > data["usd_inr"]["Close"].iloc[-4]:
    india_score += 1
    notes.append("USD-INR short-term uptrend intact")

# Sentiment
if data["nifty"]["pct"].iloc[-1] < -0.5:
    sentiment_score += 1
    notes.append("Indian equities weak → risk-off sentiment")

if data["india_vix"]["pct"].iloc[-1] > 5:
    sentiment_score += 1
    notes.append("India VIX rising → safe-haven demand")

total_score = global_score + india_score + sentiment_score

if total_score >= 6:
    bias = "Strong Bullish"
elif total_score >= 3:
    bias = "Bullish"
elif total_score >= 0:
    bias = "Neutral"
else:
    bias = "Bearish"

if bias in ["Strong Bullish", "Bullish"]:
    outlook = "Gold likely to remain supported over the next 3–7 days."
elif bias == "Neutral":
    outlook = "Gold may remain range-bound in the near term."
else:
    outlook = "Gold may face short-term pressure."

suggestion = (
    "Favorable for ETF SIP / partial buy"
    if total_score >= 3 else
    "Wait, avoid aggressive buying"
)

report = {
    "date": str(date.today()),
    "score": total_score,
    "bias": bias,
    "outlook": outlook,
    "suggestion": suggestion,
    "notes": notes
}

with open(f"{HISTORY_DIR}/{date.today()}.json", "w") as f:
    json.dump(report, f, indent=2)

html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gold Daily Brief</title>
<style>
body {{ font-family: Arial; background:#f4f4f4; padding:15px; }}
.card {{ background:white; padding:15px; border-radius:10px; margin-bottom:12px; }}
</style>
</head>
<body>
<h2>Gold Daily Brief – {date.today()}</h2>

<div class="card"><b>Score:</b> {total_score} <br><b>Bias:</b> {bias}</div>

<div class="card">
<b>Key Factors</b>
<ul>
{''.join(f"<li>{n}</li>" for n in notes)}
</ul>
</div>

<div class="card"><b>3–7 Day Outlook</b><br>{outlook}</div>
<div class="card"><b>Suggestion</b><br>{suggestion}</div>

</body>
</html>
"""

with open(f"{OUTPUT_DIR}/index.html", "w") as f:
    f.write(html)

print("Gold report generated")
