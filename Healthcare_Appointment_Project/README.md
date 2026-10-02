# CarePlus Complete Student Project

## Run
1. MySQL Workbench: `CREATE DATABASE healthcare_appointment_db;`
2. Open terminal in the project root.
3. Create venv: `python -m venv backend/venv`
4. Activate Windows: `backend\venv\Scripts\activate`
5. Install: `pip install -r backend/requirements.txt`
6. If MySQL password is not `root`, set `DATABASE_URL`.
7. Run: `uvicorn backend.main:app --reload --port 8002`
8. Open: http://127.0.0.1:8000/app/
9. Swagger: http://127.0.0.1:8000/docs

## Default admin
admin1@careplus.com / Admin@123
admin2@careplus.com / Admin@123

## Notes
The backend automatically creates tables and seed doctors/admins. Appointment limit is 10 active appointments per doctor/day. Same-day multiple doctors are allowed only when times do not overlap. Holidays block booking. Payment is demo-only and creates receipts. This is a student project, not a production medical system.
