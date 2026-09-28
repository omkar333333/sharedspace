# 🤝 SharedSpace

**A full-featured peer-to-peer resource sharing, item lending, and community booking platform.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web_Framework-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-D71F00?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?style=flat&logo=render&logoColor=white)](https://render.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Features

- 👤 **User Authentication & Trust Metrics**: Secure registration, password hashing (bcrypt), community ratings, and dynamic trust scores.
- 📦 **Resource Listings & Categorization**: Post items to lend or sell with photos, availability schedules, and category filters.
- 📅 **Booking & Lending Workflow**: Reservation requests, status management (Pending, Approved, Completed), and return tracking.
- 💬 **Integrated Direct Messaging**: In-platform communication between borrowers and resource owners.
- 🚀 **Cloud Ready**: Configured for instant deployment on **Render** using Gunicorn and `render.yaml`.

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask, Flask-Login, Flask-WTF
- **Database**: SQLite / PostgreSQL with SQLAlchemy ORM & Alembic migrations
- **Frontend**: Jinja2 Templates, HTML5, CSS3, JavaScript
- **Deployment**: Render, Gunicorn, Procfile

---

## 🚀 Quickstart & Setup

### 1. Clone the repository
```bash
git clone https://github.com/omkar333333/sharedspace.git
cd sharedspace
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
python init_db.py
python seed.py
```

### 5. Launch the application
```bash
python run.py
```
Open your browser and navigate to `http://localhost:5000`.

---

## 👨‍💻 Author

**Omkar Mote**  
- 🎓 *B.E. in Artificial Intelligence & Data Science*  
- 🌐 [GitHub Profile](https://github.com/omkar333333)
