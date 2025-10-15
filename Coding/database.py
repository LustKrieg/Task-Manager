# Database
import sqlite3
from datetime import datetime


DATABASE_NAME = "tasks.db"

# Function 0 -- Getting the Connection
def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    return conn

get_connection()

# Function 1 -- Creating the table, organazing data
def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Function 2 -- Add a new task to the database
def add_task(title):
    if not title.strip():
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO tasks (title, completed, created_at)
        VALUES (?, ?, ?)
    ''', (title.strip(), 0, created_at))
    
    conn.commit()
    conn.close()
    return True

# Function 3 -- Show Me What's Not Done 
def get_active_tasks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, title FROM tasks
        WHERE completed = 0
        ORDER BY created_at DESC
    ''')
    
    tasks = cursor.fetchall()
    conn.close()
    return tasks

# Function 4 -- Show Me What's Done 
def get_completed_tasks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM tasks
        WHERE completed = 1
        ORDER BY created_at DESC
    ''')

    tasks = cursor.fetchall()
    conn.close()
    return tasks

# Function 5 -- Check It Off
def mark_complete(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE tasks
        SET completed = 1
        WHERE id = ?
    ''', (task_id,))  # ✅ FIXED: must be (task_id,) not (task_id)

    conn.commit()
    conn.close()

  # cursor.execute(f'... WHERE id = {task_id}')  # ❌ Hackable!

# Function 6 -- Remove It Forever
def delete_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM tasks 
        WHERE id = ?
    ''', (task_id,))
    
    conn.commit()
    conn.close()

create_table()