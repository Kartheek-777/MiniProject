# PlacementCopilot - AI-Powered Placement Intelligence & Career Copilot

An enterprise-grade web application tailored for engineering students to analyze resumes against job descriptions, identify critical technical skill gaps, generate structured career roadmaps, prepare for mock interviews, and track placement readiness.

---

## 🛠️ Phase 1 Architecture Overview

Built using **Python 3.10+**, **Django 5.0**, **MySQL** (via `pymysql`), **Bootstrap 5**, and **Vanilla JS**.

### Modular Django Application Architecture

The application is decomposed into **7 modular domain apps** to ensure high maintainability and clean separation of concerns:

1. **`accounts`**: User authentication (register, login, logout), student profile management (`UserProfile` model storing department, graduation year, target role).
2. **`dashboard`**: Main placement intelligence dashboard providing an aggregated overview of student metrics and quick navigation cards.
3. **`resume_analyzer`**: Upload and parser module for student resumes (PDF/DOCX) to evaluate ATS compliance and extract key technical skills.
4. **`job_matcher`**: Job Description (JD) matching engine that calculates skill overlap scores and identifies missing keywords.
5. **`career`**: Personalized career copilot for generating structured learning paths based on target engineering roles (SDE, Data Engineering, DevOps, Embedded Systems).
6. **`interview`**: Interactive mock interview simulation app for technical (DSA, OS, DBMS) and HR behavioral interview practice.
7. **`ai_engine`**: Isolated AI pipeline abstraction layer wrapper for LLM services (Gemini / OpenAI). Isolating this logic prevents LLM changes from breaking core business apps.

---

## 🔄 Request Flow (Browser → URL → View → Template)

```
[Browser Request] 
      │
      ▼
[placement_copilot/urls.py] ──(include)──► [app/urls.py]
                                                 │
                                                 ▼
[Rendered HTML Response] ◄──(Context)─── [app/views.py] ◄──► [app/models.py] (MySQL)
                                                 │
                                                 ▼
                                        [templates/base.html]
                                                 │
                                                 ▼
                                        [app/template.html]
```

1. **Client Request**: Browser requests a route (e.g., `GET /dashboard/`).
2. **Root Dispatcher (`placement_copilot/urls.py`)**: Routes request based on path prefix to `dashboard/urls.py`.
3. **App Dispatcher (`dashboard/urls.py`)**: Maps matching path to `views.dashboard_home`.
4. **View Execution (`dashboard/views.py`)**: Validates authentication via `@login_required`, fetches model state from MySQL database, and builds context.
5. **Template Rendering (`templates/dashboard/index.html`)**: Extends `templates/base.html`, injects Bootstrap 5 dynamic elements, and returns full HTML back to client.

---

## ⚙️ Environment Variables Configuration (`.env`)

Environment configuration is managed securely using `python-dotenv`:

```ini
# Secret key for Django
SECRET_KEY=django-insecure-placement-copilot-dev-key

# Debug Mode
DEBUG=True

# Database Configuration (MySQL)
DB_ENGINE=django.db.backends.mysql
DB_NAME=placement_copilot_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306

# Fallback setting for local SQLite testing
USE_SQLITE_FALLBACK=True
```

---

## 🚀 Step-by-Step Setup & Running Instructions

### 1. Prerequisite Check
Ensure Python 3.10+ is installed on your system.

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Create MySQL Database (or local fallback)
Create a MySQL database named `placement_copilot_db` on your local MySQL server:
```sql
CREATE DATABASE placement_copilot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Run Django Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Start Development Server
```bash
python manage.py runserver
```

### 6. Access Application Routes
- **Landing Page**: `http://127.0.0.1:8000/`
- **Registration**: `http://127.0.0.1:8000/accounts/register/`
- **Login**: `http://127.0.0.1:8000/accounts/login/`
- **Student Dashboard**: `http://127.0.0.1:8000/dashboard/`

---

## 🧪 Technical Interview Summary Points

- **Why Modular Apps?** Prevents a monolithic "spaghetti" codebase by grouping features into domain-specific apps (`accounts`, `resume_analyzer`, `ai_engine`, etc.).
- **Why PyMySQL?** Enables seamless MySQL connectivity in Python environments without requiring native MySQL C compiler dependencies on Windows.
- **Why AI Engine Abstraction?** Separates LLM API callers from core business views, ensuring high testability and flexibility when switching or upgrading AI models.
