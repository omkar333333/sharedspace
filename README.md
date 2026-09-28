<div align="center">

# 🤝 SharedSpace

**A full-stack peer-to-peer resource sharing, item lending, and community booking platform.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web_Framework-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

<p align="center">
  <a href="https://omkar-portfolio-live.vercel.app"><img src="https://img.shields.io/badge/🌐_Portfolio-Live_Site-0A66C2?style=for-the-badge&logo=vercel&logoColor=white" /></a>
  <a href="https://github.com/omkar333333"><img src="https://img.shields.io/badge/Status-Open_to_Internships_&_Roles-brightgreen?style=for-the-badge" /></a>
  <a href="mailto:your-email@example.com"><img src="https://img.shields.io/badge/Email-Direct_Contact-blue?style=for-the-badge&logo=gmail&logoColor=white" /></a>
</p>

<p align="center">
  <a href="#-recruiter--hiring-manager-quick-summary-tldr">📌 Recruiter Summary</a> •
  <a href="#-key-features">✨ Key Features</a> •
  <a href="#-system-architecture--workflow">🏗️ Architecture</a> •
  <a href="#-tech-stack">🛠️ Tech Stack</a> •
  <a href="#-quickstart--local-setup">🚀 Quickstart</a>
</p>

</div>

---

> [!TIP]
> ### 📌 Recruiter & Hiring Manager Quick Summary (TL;DR)
> - **Developer**: **Omkar Mote** — *B.E. in Artificial Intelligence & Data Science* (Pune, India)
> - **Core Stack**: Python, Flask, Flask-Login, SQLAlchemy ORM, SQLite/PostgreSQL, Jinja2, HTML5/CSS3/JavaScript, Render.
> - **Problem Solved**: Reduces equipment waste and optimizes campus resource sharing by providing a peer-to-peer rental, reservation, and community trust-scoring platform.
> - **Key Engineering Highlights**:
>   - 🛡️ **Security & Identity**: Bcrypt-hashed password storage, session management, CSRF protection via Flask-WTF.
>   - 🗄️ **Relational Modeling**: Clean normalized schema tracking users, categories, listings, reservation state machines (Pending ➔ Approved ➔ Returned), and peer ratings.
>   - 🚀 **Cloud Infrastructure**: Fully containerized and configured with Gunicorn WSGI and `render.yaml` for production deployment.
> - **Direct Contact**: [GitHub Profile](https://github.com/omkar333333) • [Live Portfolio Website](https://omkar-portfolio-live.vercel.app)

---

## ✨ Key Features

- 👤 **Secure User Authentication & Profiles**: Registration, encrypted credentials (bcrypt), user avatars, and activity tracking.
- ⭐ **Dynamic Community Trust Scores**: Weighted ratings and reviews calculated dynamically per user transaction to promote accountability.
- 📦 **Resource Listings & Categorization**: Multi-category catalogue (Electronics, Academic Books, Tools, Sports) with photo uploads and status tags.
- 📅 **Interactive Lending Workflow & State Machine**:
  - Borrowers submit reservation date ranges.
  - Owners approve, decline, or complete lending cycles.
  - Automatic collision detection prevents double-booking of active items.
- 💬 **Integrated Direct Messaging**: Built-in messaging thread between borrowers and resource owners.
- ☁️ **Cloud Deployment Ready**: Pre-configured for deployment on **Render** with Gunicorn and automated database seeding.

---

## 🏗️ System Architecture & Workflow

```text
       ┌────────────────────────┐
       │   Browser Client (UI)  │
       │  HTML5 / CSS3 / Jinja2 │
       └───────────┬────────────┘
                   │ HTTP / REST Requests
                   ▼
       ┌────────────────────────┐
       │     Flask App Router   │
       │ (Auth, Listings, Book) │
       └───────────┬────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
┌──────────────────┐  ┌──────────────────┐
│ Flask-Login /    │  │  SQLAlchemy ORM  │
│ Bcrypt Security  │  │  (Data Engine)   │
└──────────────────┘  └────────┬─────────┘
                               │
                               ▼
                      ┌──────────────────┐
                      │ SQLite / Postgres│
                      │ Database Engine  │
                      └──────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Backend** | Python 3.10+, Flask, Flask-Login, Flask-WTF, WTForms |
| **Database & ORM** | SQLAlchemy, SQLite (Dev) / PostgreSQL (Prod), Alembic Migrations |
| **Frontend** | Jinja2 Templates, HTML5, CSS3, JavaScript (Vanilla), Feather Icons |
| **Security** | Bcrypt password encryption, CSRF protection, Session management |
| **Hosting & DevOps** | Render, Gunicorn WSGI, Git, Procfile |

---

## 🚀 Quickstart & Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/omkar333333/sharedspace.git
cd sharedspace
```

### 2. Create and activate a virtual environment
```bash
# Windows (PowerShell)
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

### 4. Initialize and Seed the Database
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

## 📁 Repository Structure

```text
sharedspace/
├── app/
│   ├── models.py         # SQLAlchemy relational database models
│   ├── routes/           # Blueprint route controllers (auth, listings, bookings)
│   ├── templates/        # Responsive Jinja2 HTML templates
│   └── static/           # CSS stylesheets, JavaScript files & icons
├── init_db.py            # Database table creation script
├── seed.py               # Sample category and listing data seeder
├── run.py                # Main application entry point
├── Procfile              # Production process declaration
├── requirements.txt      # Python runtime dependencies
└── render.yaml           # Infrastructure-as-code configuration for Render
```

---

## 👨‍💻 Author

**Omkar Mote**  
- 🎓 *B.E. in Artificial Intelligence & Data Science*  
- 🌐 [Live Portfolio Website](https://omkar-portfolio-live.vercel.app)  
- 💻 [GitHub Profile](https://github.com/omkar333333)
