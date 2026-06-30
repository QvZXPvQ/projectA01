import sqlite3
import os

DB_PATH = os.getenv("DATABASE_URL", "bot.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            owner_id INTEGER,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            assignee_id INTEGER,
            deadline TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'todo',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        );
    """)

    conn.commit()
    conn.close()
    print("Baza danych gotowa!")

# ── UŻYTKOWNICY ──────────────────────────────────────────
def save_user(telegram_id, username, first_name):
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO users (telegram_id, username, first_name)
        VALUES (?, ?, ?)
    """, (telegram_id, username, first_name))
    conn.commit()
    conn.close()

# ── PROJEKTY ─────────────────────────────────────────────
def create_project(name, owner_id, description=""):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO projects (name, description, owner_id) VALUES (?, ?, ?)",
        (name, description, owner_id)
    )
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return project_id

def get_projects(owner_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM projects WHERE owner_id=? AND status='active' ORDER BY created_at DESC",
        (owner_id,)
    ).fetchall()
    conn.close()
    return rows

def get_project(project_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    conn.close()
    return row

# ── ZADANIA ──────────────────────────────────────────────
def create_task(project_id, title, deadline=None, priority="medium"):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO tasks (project_id, title, deadline, priority) VALUES (?, ?, ?, ?)",
        (project_id, title, deadline, priority)
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_tasks(project_id=None, status=None):
    conn = get_connection()
    query = "SELECT t.*, p.name as project_name FROM tasks t LEFT JOIN projects p ON t.project_id=p.id WHERE 1=1"
    params = []
    if project_id:
        query += " AND t.project_id=?"
        params.append(project_id)
    if status:
        query += " AND t.status=?"
        params.append(status)
    query += " ORDER BY t.created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows

def get_todays_tasks():
    conn = get_connection()
    rows = conn.execute("""
        SELECT t.*, p.name as project_name
        FROM tasks t
        LEFT JOIN projects p ON t.project_id=p.id
        WHERE t.status != 'done'
        ORDER BY
            CASE t.priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
            END
    """).fetchall()
    conn.close()
    return rows

def get_overdue_tasks():
    conn = get_connection()
    rows = conn.execute("""
        SELECT t.*, p.name as project_name
        FROM tasks t
        LEFT JOIN projects p ON t.project_id=p.id
        WHERE t.deadline < date('now') AND t.status != 'done'
        ORDER BY t.deadline ASC
    """).fetchall()
    conn.close()
    return rows

def update_task_status(task_id, status):
    conn = get_connection()
    conn.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
    conn.commit()
    conn.close()

def update_task_priority(task_id, priority):
    conn = get_connection()
    conn.execute("UPDATE tasks SET priority=? WHERE id=?", (priority, task_id))
    conn.commit()
    conn.close()

def assign_task(task_id, assignee_id):
    conn = get_connection()
    conn.execute("UPDATE tasks SET assignee_id=? WHERE id=?", (assignee_id, task_id))
    conn.commit()
    conn.close()

def get_task(task_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return row
