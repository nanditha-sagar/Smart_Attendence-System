# 📸 Smart Face Attendance System

An AI-powered automated attendance tracking and analytics platform built with **Python**, **OpenCV (Haar Cascade & LBPH Face Recognizer)**, **Flask**, **SQLite**, **Pandas**, and a **Modern Web Interface**.

---

## 🌟 Key Features

- **Automated Face Recognition Attendance**: Real-time facial detection and recognition using Haar Cascade Classifiers and LBPH (Local Binary Patterns Histograms).
- **Live Video Streaming**: Real-time camera feed streamed directly into the dashboard with bounding boxes and recognition status overlays.
- **Relational SQLite Database**: Auto-initialized database tracking registered students, attendance logs, and administrative credentials with duplicate check-in prevention.
- **Modern Responsive Dashboard**:
  - Live metric stat cards (Total Students, Present Today, Absent Today, Compliance Rate).
  - Searchable real-time attendance table with status pill badges.
  - Manual check-in and camera scanner toggle.
- **Student Management Directory**: Register new students, update profiles, and manage facial enrollment datasets.
- **Analytics & Reporting**:
  - Monthly attendance summaries and compliance percentages with progress bars.
  - One-click CSV export for offline spreadsheets.
  - Standalone Pandas data science reporting scripts.

---

## 📁 Project Architecture

```
Smart_Attendence-System/
│
├── backend/
│   ├── app.py                      # Flask backend API server & static frontend host
│   ├── attendance.py               # Attendance tracking service connected to SQLite
│   ├── camera.py                   # OpenCV webcam handler & live video streaming generator
│   ├── capture_faces.py            # CLI tool to capture student face dataset
│   ├── face_detector.py            # Haar Cascade face detection engine with auto-fallback
│   ├── face_recognizer.py          # LBPH face recognizer with dynamic database label mapping
│   ├── register_face.py            # Automated face sample capture and instant retraining
│   ├── test_recognition.py         # Standalone desktop OpenCV face recognition tester
│   ├── train_model.py              # Face dataset trainer generating face_model.yml
│   ├── test_system.py              # Automated 12-point unit and integration test suite
│   ├── requirements.txt            # Python dependencies
│   │
│   ├── database/
│   │   ├── create_tables.sql       # Relational schema (users, students, attendance)
│   │   ├── db_config.py            # SQLite connection helper & seed generator
│   │   └── queries.py              # Student, attendance, report, and auth SQL queries
│   │
│   ├── datasets/users/             # Student face image datasets (organized by student ID)
│   ├── models/
│   │   ├── face_model.yml          # Trained LBPH face model weights
│   │   └── haarcascade_frontalface_default.xml # Haar Cascade classifier
│   │
│   └── utils/
│       ├── helpers.py              # Datetime, CSV, and standardized JSON response utilities
│       ├── image_utils.py          # Face cropping, lighting equalization, and normalization
│       └── logger.py               # Centralized logging configuration
│
├── frontend/
│   ├── index.html                  # Administrative sign-in page
│   ├── dashboard.html              # Live monitoring dashboard with camera feed & stats
│   ├── students.html               # Student registration and directory
│   ├── reports.html                # Monthly attendance analytics and CSV exports
│   ├── css/
│   │   └── style.css               # Modern design system stylesheet
│   └── js/
│       ├── api.js                  # Dynamic API client & toast notifications
│       ├── auth.js                 # Authentication & session management
│       ├── dashboard.js            # Live dashboard logic, camera stream & table filter
│       ├── students.js             # Student enrollment and CRUD operations
│       └── reports.js              # Monthly calculation and progress bar renderer
│
├── analytics/
│   ├── attendance_analysis.py      # Pandas attendance statistics script
│   ├── export_csv.py               # Database to CSV exporter
│   └── monthly_report.py           # Monthly summary data breakdown
│
└── docs/                           # Architecture diagrams and project documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** installed on your system.

### 2. Environment Setup & Dependencies

In your PowerShell / Command Prompt terminal, navigate to the project directory:

```powershell
# Navigate to the project root
cd "c:\Users\AN_Nanditha\OneDrive\Desktop\other p\Smart_Attendence-System"

# Activate the virtual environment (or use system Python)
.\venv\Scripts\activate

# Install required dependencies
pip install -r backend/requirements.txt
```

### 3. Initialize Database & Train Face Model

```powershell
# Initialize SQLite database schema and seed default data
python -c "from backend.database.db_config import init_db; init_db()"

# Train the face recognizer on existing face dataset
python backend/train_model.py
```

### 4. Run the Web Application

```powershell
python backend/app.py
```

Open your browser and navigate to:
👉 **[http://localhost:5000](http://localhost:5000)**

- **Default Admin Credentials**:
  - **Username**: `admin`
  - **Password**: `admin123`

---

## 🧪 Running System Tests

To verify that all components, database queries, face recognition models, and HTTP routes are working correctly:

```powershell
python backend/test_system.py
```
*(All 12 automated unit and integration tests will execute and report `OK`)*

---

## 📊 Analytics & Reporting Scripts

You can also run standalone data science and reporting scripts:

```powershell
# 1. Export database records to CSV
python analytics/export_csv.py

# 2. Compute attendance percentage and generate analytics
python analytics/attendance_analysis.py

# 3. Generate detailed monthly summary breakdown
python analytics/monthly_report.py
```

---

## 📷 Registering New Student Faces

To enroll a new student with live facial scanning:

1. Add the student via the web interface at **[http://localhost:5000/students.html](http://localhost:5000/students.html)**. Note their **Student ID**.
2. Run the interactive face capture tool:
   ```powershell
   python backend/register_face.py
   ```
3. Enter the Student ID. Look at your webcam and press **C** to capture face samples (or let auto-capture capture 20 samples). The system will automatically crop, normalize, and retrain the model.
