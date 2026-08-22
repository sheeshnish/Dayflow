# Dayflow Final Hackathon Product

Frontend: HTML/CSS/JS
Backend: Python + Flask
Database: SQLite (SQL) for zero-setup demo

## Run
1. Open a terminal in `backend`.
2. `python -m venv .venv`
3. Windows: `.venv\Scripts\activate`
4. macOS/Linux: `source .venv/bin/activate`
5. `pip install -r requirements.txt`
6. `python app.py`
7. Open http://127.0.0.1:5000

The backend creates and seeds `dayflow.db` automatically.

## Demo accounts
Employee: OIAnSh2025001 / Dayflow@123
Admin: OIAdMi2020001 / Admin@123
Admin invite code: DAYFLOW-ADMIN

## Final architecture
Browser -> Flask API -> SQL database

The frontend no longer decides whether a password, role, attendance, leave decision or payroll change is valid. Python processes those actions and writes the results to the database.
