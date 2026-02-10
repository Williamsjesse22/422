# Photo Gallery (Flask)

Small Flask app to upload and display photos; stores metadata in a MySQL-compatible database (your AWS RDS).

## Prerequisites
- Python 3.8+
- An AWS RDS MySQL/Aurora instance (or other MySQL-compatible DB)

## Install

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

### Testing 
```powershell
python app.py
# then open http://127.0.0.1:5000
```

### Production
```powershell
flask run --host=0.0.0.0
# then open http://<your_ip>:5000
```

Notes
- The app calls `ensure_table()` on the index route to create the `photos` table if missing.
- Make sure your RDS Security Group allows inbound TCP port 3306 from your machine's public IP. If you cannot open the DB publicly, run the app from an EC2 in the same VPC or use an SSH tunnel.
- If your RDS requires SSL, update `get_connection()` in `app.py` to pass the `ssl` parameter to `pymysql.connect()` (I can help with this if needed).

Troubleshooting
- Connection timeout / refused: verify `DB_HOST`, port 3306, and Security Group.
- Authentication errors: verify `DB_USER` / `DB_PASSWORD` and that the user has privileges on `DB_NAME`.
- File uploads not showing: ensure `static/uploads` exists or is writable; uploaded files are saved there.
