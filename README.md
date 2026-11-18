# FIR Management System

Audio complaint → NLP extraction → Editable form → MySQL storage

---

## Project Structure

```
fir_system/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py        reads .env
│   │   ├── database.py      SQLAlchemy + MySQL
│   │   ├── models.py        ORM table + Pydantic schemas
│   │   ├── ml_models.py     loads Whisper, Flan-T5, spaCy once
│   │   ├── pipeline.py      full NLP pipeline
│   │   ├── routes.py        all API endpoints
│   │   └── main.py          FastAPI app
│   ├── .env                 DB credentials ← edit this
│   ├── requirements.txt
│   └── run.py               ← START SERVER
└── frontend/
    └── index.html           complete UI (served by FastAPI)
```

---

## Step 1 — MySQL Setup

```sql
CREATE DATABASE fir_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## Step 2 — Configure .env

Edit `backend/.env`:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=fir_db
```

---

## Step 3 — Install dependencies (once)

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

## Step 4 — Start the server

```bash
cd backend
python run.py
```

---

## Step 5 — Open the app

Visit: **http://localhost:8000**

---

## How to use

1. Click **File Complaint**
2. Upload an MP3/WAV audio file
3. Click **Extract FIR from Audio**
4. Wait ~30–60 seconds for transcription
5. Review and edit all fields in the form
6. Click **Save FIR to Database**
7. Click **All Records** to view, search and manage saved FIRs

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | /api/extract | Upload audio → FIR preview JSON |
| POST | /api/fir | Save FIR to MySQL |
| GET | /api/fir | List all FIRs |
| GET | /api/fir/{id} | Get single FIR |
| PUT | /api/fir/{id} | Update FIR |
| DELETE | /api/fir/{id} | Delete FIR |

Swagger docs: **http://localhost:8000/docs**
