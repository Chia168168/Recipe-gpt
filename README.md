# TENG 食譜系統 - Flask + PostgreSQL (converted from Google Apps Script)

This repository is an automatic conversion of your original Google Apps Script backend (code.gs) and the existing front-end (index.html).
It provides a Flask backend with REST endpoints and the original front-end (1:1) adjusted to call the backend.

## How to deploy
1. Push this repo to GitHub.
2. Create a Web Service on Render (or similar), set `DATABASE_URL` environment variable to your Postgres connection string.
3. Render will run `pip install -r requirements.txt` and start `gunicorn app:app`.

## Notes
- The original `index.html` is preserved with a compatibility shim so existing `google.script.run` calls continue to work (routed to the Flask API).
- A CSV legacy importer endpoint is available: `POST /api/import_legacy_csv` (form-data file field `file`) to import exported Google Sheet CSVs and convert them to JSON recipes.
