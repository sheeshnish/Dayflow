# Dayflow — Online-version starter

This package is the exact uploaded Dayflow frontend plus the Python backend needed to process its API calls.

## Folder layout

frontend/
  index.html

backend/
  app.py
  requirements.txt
  .env.example

database/
  schema.sql

## Run locally

1. Open a terminal in `backend`.
2. Create a virtual environment:

Windows:
`py -m venv .venv`
`.venv\Scripts\activate`

macOS/Linux:
`python3 -m venv .venv`
`source .venv/bin/activate`

3. Install:

`pip install -r requirements.txt`

4. Run:

`python app.py`

5. Open:

`http://127.0.0.1:5000`

The server automatically creates `dayflow.db`, tables, and demo data on first run.

## Demo logins

Employee:
OIAnSh2025001 / Dayflow@123

Admin:
OIAdMi2020001 / Admin@123

## GitHub

Copy this entire project into your `online-version` branch.

Then:

git add .
git commit -m "Add Dayflow Python backend"
git push origin online-version

## Next cloud step

After the local version works, replace the SQLite connection with a hosted PostgreSQL connection and deploy the Flask backend. The frontend already calls `/api/...`, so it is structured for this transition.
