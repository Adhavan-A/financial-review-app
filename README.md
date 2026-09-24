# AI Financial Review System - NYC Restaurant Co. 

An AI-native full-stack application designed to automate financial data ingestion, categorization, and variance analysis for NYC Restaurant Co. This system leverages Large Language Models (LLMs) to replace manual data entry and provide intelligent financial insights.

##  Features

- **Data Ingestion:** Upload monthly transaction data via Excel (`.xlsx`).
- **AI Categorization:** Automatically categorizes uncategorized transactions (Revenue, COGS, Payroll, OpEx, Other) using Google Gemini AI.
- **Deterministic P&L Calculation:** Generates accurate monthly Profit & Loss reports using strict math rules.
- **AI Variance Analysis:** Compares month-over-month financial data and provides an AI-generated explanation of material changes.
- **AI Financial Analyst Chatbot:** An interactive chat interface to ask specific queries regarding the P&L data.
- **Modern UI:** A clean, responsive Glassmorphism frontend dashboard.

##  Tech Stack

- **Backend:** Python, FastAPI, SQLite (SQLAlchemy)
- **Data Processing:** Pandas, Openpyxl
- **AI Integration:** Google Gemini API (`gemini-3.5-flash`)
- **Frontend:** HTML5, CSS3 (Glassmorphism), Vanilla JavaScript

##  Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <your-github-repo-url>
   cd financial-review-app