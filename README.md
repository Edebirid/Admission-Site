# School Pupil Admission Portal (Starter)

A beginner-friendly Flask web application with:
- Parent/guardian registration and login
- Secure password hashing
- CSRF protection on forms
- Pupil admission application form
- Applicant dashboard and application status
- Admin-only application list and status review
- SQLite database for local development

## Requirements
- Python 3.10 or newer
- VS Code (optional, but recommended)

## Setup in VS Code

Open this folder in VS Code, then open Terminal > New Terminal.

### Windows
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app init-db
python -m flask --app app create-admin
python -m flask --app app run
```

If PowerShell blocks activation, you can use Command Prompt and run:
```bat
.venv\Scripts\activate.bat
```

Open http://127.0.0.1:5000 in your browser.

### macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app app init-db
python -m flask --app app create-admin
python -m flask --app app run
```

The `create-admin` command asks for an admin name, email and password. Use a unique password of at least 12 characters. Do not make a public admin registration page.

## Important security steps before putting this online
1. Set a long, random `SECRET_KEY` environment variable. The development fallback in `app.py` is not safe for production.
2. Use HTTPS and set `COOKIE_SECURE=1`.
3. Turn debug mode off. Never expose Flask's development server to the public internet.
4. Use a production WSGI server and a reputable host; configure backups, monitoring and updates.
5. Add rate limiting, email verification, password reset, and an appropriate privacy notice before real public use.
6. Collect only necessary pupil data, restrict staff access, and protect/backup the database. Follow applicable Nigerian data protection requirements.
7. SQLite is fine for learning and a small local test. For a live school portal, consider PostgreSQL and managed hosting.
8. This starter does not upload documents, send emails/SMS, generate admission numbers, or perform online payments yet.

## Project layout
```text
school_admission_portal/
  app.py
  requirements.txt
  README.md
  templates/
    base.html
    index.html
    register.html
    login.html
    dashboard.html
    application.html
    admin_applications.html
    review_application.html
    error.html
  static/
    style.css
```
