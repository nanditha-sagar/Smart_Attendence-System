import sqlite3
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "attendance.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "create_tables.sql")


def get_db_connection():
    """Returns a SQLite connection with dict-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initializes database tables and default seed data if not present."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables
    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, "r") as f:
            cursor.executescript(f.read())
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                roll_number TEXT UNIQUE NOT NULL,
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                department TEXT DEFAULT 'Computer Science',
                photo_path TEXT DEFAULT '',
                face_encoding TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Present',
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE(student_id, date)
            );
        """)

    # Ensure existing tables have photo_path and face_encoding columns
    try:
        cursor.execute("PRAGMA table_info(students)")
        existing_cols = [col[1] for col in cursor.fetchall()]
        if "photo_path" not in existing_cols:
            cursor.execute("ALTER TABLE students ADD COLUMN photo_path TEXT DEFAULT ''")
        if "face_encoding" not in existing_cols:
            cursor.execute("ALTER TABLE students ADD COLUMN face_encoding TEXT DEFAULT ''")
    except Exception:
        pass

    # Seed admin user if not exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "admin123", "admin")
        )

    # Seed default students if empty
    cursor.execute("SELECT COUNT(*) as count FROM students")
    if cursor.fetchone()["count"] == 0:
        default_students = [
            (101, "Nanditha Sagar", "CS101", "nanditha@example.com", "9876543210", "Computer Science"),
            (1, "Rahul Sharma", "CS102", "rahul@example.com", "9876543211", "Computer Science"),
            (2, "Anita Roy", "CS103", "anita@example.com", "9876543212", "Information Technology"),
        ]
        cursor.executemany(
            "INSERT INTO students (id, name, roll_number, email, phone, department) VALUES (?, ?, ?, ?, ?, ?)",
            default_students
        )

        # Seed sample attendance history for reports and analytics
        today = datetime.now()
        for i in range(1, 10):
            past_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            # Alternate attendance for realistic analytics
            cursor.execute(
                "INSERT OR IGNORE INTO attendance (student_id, date, time, status) VALUES (?, ?, ?, ?)",
                (101, past_date, "09:02:15", "Present")
            )
            cursor.execute(
                "INSERT OR IGNORE INTO attendance (student_id, date, time, status) VALUES (?, ?, ?, ?)",
                (1, past_date, "09:05:40", "Present" if i % 2 == 0 else "Absent")
            )
            cursor.execute(
                "INSERT OR IGNORE INTO attendance (student_id, date, time, status) VALUES (?, ?, ?, ?)",
                (2, past_date, "09:11:00", "Present" if i % 3 != 0 else "Absent")
            )

    conn.commit()
    conn.close()
    return True


if __name__ == "__main__":
    init_db()
    print(f"[SUCCESS] Database initialized successfully at: {DB_PATH}")
