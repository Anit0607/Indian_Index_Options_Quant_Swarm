import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Quant Swarm Control Tower")

@app.get("/", response_class=HTMLResponse)
def read_root():
    for p in ["index.html", "public/index.html"]:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
    return "<h1>Quant Swarm Control Tower</h1>"

@app.get("/api/status")
def get_status():
    return {
        "status": "operational",
        "active_agents": 6,
        "capital_nav": 500000,
        "max_risk_pct": 2.0,
        "margin_utilization_pct": 28.4,
        "compliance": "SEBI_DISCRETIONARY_HITL"
    }
