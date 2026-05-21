# MoneyInsight

MoneyInsight is a Telegram bot that analyzes a Kaspi Gold PDF statement. The user sends a PDF file, and the bot returns income, expenses, real account balance, category statistics, recent transactions, and history.

## Main features

- Upload and analyze Kaspi PDF statements
- Calculate total income, expenses, and real account balance from the PDF
- Categorize spending by merchant
- Show expenses by category with operation counts
- Show statistics and recent transactions
- Save reports and transactions in SQLite
- Learn unknown merchants from user feedback
- Keep working even if AI categorization is unavailable

## Project structure

```text
MoneyInsight_Final/
├── main.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── .env.example
├── FINAL_CRITERIA_MATCH.md
├── data/
│   └── merchants.json
└── money_insight/
    ├── bot.py                  # launcher only
    ├── handlers.py             # Telegram handlers
    ├── report_utils.py         # calculations and formatting
    ├── balance_reader.py       # account balance extraction from PDF
    ├── config.py
    ├── database.py
    ├── pdf_reader.py
    ├── ai_classifier.py
    ├── charts.py
    └── keyboards/
        ├── inline_keyboards.py
        ├── main_menu.py
        └── start_menu.py
```

## Setup

1. Create and activate a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create `.env` from the example.

```bash
cp .env.example .env
```

4. Add your Telegram BotFather token to `.env`.

```env
BOT_TOKEN=your_token_here
```

5. Optional: add `OPENROUTER_API_KEY` if you want AI categorization for unknown merchants.

## Run locally

```bash
python main.py
```

Then open Telegram, send `/start`, and upload a Kaspi Gold PDF statement.

## Deployment notes

The project includes `Procfile` and `runtime.txt`, so it can be deployed as a Python worker on Render, Railway, VPS, or another hosting service.

For Render/Railway:

- Build command: `pip install -r requirements.txt`
- Start command: `python main.py`
- Add environment variable: `BOT_TOKEN`
- Optional environment variable: `OPENROUTER_API_KEY`

## Presentation outline

1. Project title: MoneyInsight
2. Problem: users do not easily understand where their Kaspi money goes
3. Technologies: Python, aiogram, pdfplumber, matplotlib, SQLite, OpenRouter AI optional
4. Main features: PDF analysis, categories, statistics, history, merchant learning
5. Database: users, reports, transactions
6. Demo: start bot, upload statement, show report, show statistics/history
7. Challenges: PDF table parsing and merchant categorization
8. Future improvements: monthly comparison, budget limits, export to Excel, web dashboard
