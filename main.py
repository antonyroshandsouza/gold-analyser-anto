import yfinance as yf
from datetime import date, datetime
import json
import os

OUTPUT_DIR = "output"
HISTORY_DIR = "output/history"

os.makedirs(HISTORY_DIR, exist_ok=True)

SYMBOLS = {
    "gold": "GC=F",          # Gold futures (reliable)
    "dxy": "DX-Y.NYB",
    "usd_inr": "USDINR=X",
    "us10y": "^TNX",
    "nifty": "^NSEI",
    "india_vix": "^INDIAVIX"
}

def fetch(symbol):
    df = yf.download(
        symbol,
        period="10d",
        interval="1d",
        progress=False,
        auto_adjust=True
    )
    if df.empty or len(df) < 2:
        return None
    df["pct"] = df["Close"].pct_change() * 100
    return df.dropna()

data = {k: fetch(v) for k, v in SYMBOLS.items()}

notes = []
score = 0

# -------- GLOBAL FACTORS --------
if data["dxy"] is not None and data["dxy"]["pct"].iloc[-1] < -0.3:
    score += 1
    notes.append("Dollar Index weakened → bullish for gold")

if data["us10y"] is not None and data["us10y"]["pct"].iloc[-1] < -0.5:
    score += 1
    notes.append("US bond yields falling → supports gold")

# -------- INDIA FACTORS --------
if data["usd_inr"] is not None:
    if data["usd_inr"]["pct"].iloc[-1] > 0.2:
        score += 1
        notes.append("Rupee weakened → positive for Indian gold prices")

    if len(data["usd_inr"]) >= 4:
        if data["usd_inr"]["Close"].iloc[-1] > data["usd_inr"]["Close"].iloc[-4]:
            score += 1
            notes.append("USD-INR short-term uptrend intact")

# -------- SENTIMENT --------
if data["nifty"] is not None and data["nifty"]["pct"].iloc[-1] < -0.5:
    score += 1
    notes.append("Indian equities weak → risk-off sentiment")

if data["india_vix"] is not None and data["india_vix"]["pct"].iloc[-1] > 5:
    score += 1
    notes.append("India VIX rising → safe-haven demand")

# -------- BIAS --------
if score >= 5:
    bias = "Strong Bullish"
elif score >= 3:
    bias = "Bullish"
elif score >= 1:
    bias = "Neutral"
else:
    bias = "Bearish"

outlook = {
    "Strong Bullish": "Gold likely to rise or stay strongly supported over the next 3–7 days.",
    "Bullish": "Gold likely to remain supported over the next 3–7 days.",
    "Neutral": "Gold may remain range-bound in the near term.",
    "Bearish": "Gold may face short-term pressure."
}[bias]

suggestion = (
    "Good for ETF SIP / partial buy"
    if score >= 3 else
    "Wait, avoid lump-sum buying"
)

updated_time = datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")

report = {
    "date": str(date.today()),
    "score": score,
    "bias": bias,
    "outlook": outlook,
    "suggestion": suggestion,
    "notes": notes,
    "last_updated": updated_time
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

<h2>Gold Daily Brief</h2>

<div class="card">
<b>Date:</b> {date.today()}<br>
<b>Last updated:</b> {updated_time}
</div>

<div class="card">
<b>Score:</b> {score}<br>
<b>Bias:</b> {bias}
</div>

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

print("Gold report generated successfully")
