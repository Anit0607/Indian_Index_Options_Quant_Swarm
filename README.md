# Indian Index Options Quantitative Trading Swarm

An institutional-grade, multi-agent quantitative trading system engineered for **Nifty, Bank Nifty, and Sensex Options** (Intraday & Positional), integrating **Google Gemini Swarm**, **DhanHQ APIs**, and a **Human-in-the-Loop (HITL) Dashboard on Vercel**.

## Architecture Overview

```
[Strategy Sources] (YouTube, ArXiv, PDFs)
         │
         ▼
[1. Extraction Agent]  ──▶ Standardized YAML Strategy Schema
         │
         ▼
[2. Coder Agent]       ──▶ Vectorized Python Code & AST Lookahead Bias Audit
         │
         ▼
[3. Validation Agent]  ──▶ Walk-Forward Analysis (WFA) & Deflated Sharpe Ratio (DSR)
         │
         ▼
[4. Optimizer Agent]   ──▶ Autonomous Diagnosis & Regime Conditioning (India VIX)
         │
         ▼
[5. Bouquet Agent]     ──▶ Return Correlation Matrix & Fractional Kelly Sizing
         │
         ▼
[6. Execution & RMS]   ──▶ Hard Limits (-2% Daily Stop, 70% Margin) & SEBI HITL Gate
         │
         ▼
[DhanHQ Gateway]       ──▶ Live / Paper Execution
```

## Deployment on Vercel

1. Push this repository to your GitHub account (`Anit0607/quant-options-swarm`).
2. Go to [Vercel](https://vercel.com) and click **Add New Project**.
3. Import this repository.
4. Set Framework Preset to **Other** (Root directory serves `/public/index.html` via `vercel.json`).
5. Click **Deploy**.

## Local Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
