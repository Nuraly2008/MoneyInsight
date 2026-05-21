# MoneyInsight - Final Criteria Match

Project type: Telegram Bot.

## 1. Project Idea
MoneyInsight helps users understand Kaspi Gold spending by analyzing a PDF statement in Telegram.

## 2. Commands & Navigation
Implemented:
- `/start`
- `/help`
- `/stats`
- `/transactions`
- `/history`
- `/new`
- Reply keyboard menu
- Inline buttons for report, statistics, categories, transactions, and learning unknown merchants

## 3. Features & Logic
Implemented:
- Kaspi PDF parsing with `pdfplumber`
- Income, expense, and real account balance extraction from PDF
- Expense categories
- Expense categories with operation counts
- Last transactions preview
- Largest expense
- Average daily expense
- Top spending category
- AI/rule-based merchant classification
- Bot learns unknown merchants from user choice

## 4. Database Quality
Implemented SQLite storage:
- `users`
- `reports`
- `transactions`
- Foreign keys and indexes
- Reports are preserved after bot restart

## 5. Error Handling
Implemented:
- Non-PDF file validation
- Corrupted/wrong PDF handling
- Empty transaction handling
- AI API failure fallback
- Temporary file cleanup
- Missing report messages
- Missing token message

## 6. Deployment
Included deployment files:
- `Procfile`
- `runtime.txt`
- `.env.example`

The bot can be hosted on Render, Railway, VPS, or another Python worker hosting service.

## 7. Code Quality
Improved:
- Package structure
- Separate modules for launcher, handlers, report utilities, balance reading, config, database, PDF reading, classification and keyboards
- No hardcoded secrets
- Type hints
- Docstrings
- Logging
- Reusable helper functions
