# Stock Dashboard Backend

FastAPI backend for the stock dashboard application.

## Features

- FastAPI web framework with async support
- Redis caching for performance optimization
- Stock data integration with yfinance and FinanceDataReader
- AI analysis integration with Google Gemini
- Technical indicators calculation
- RESTful API with automatic documentation

## Installation

```bash
uv sync
```

## Running

```bash
uv run uvicorn app.main:app --reload
```

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.