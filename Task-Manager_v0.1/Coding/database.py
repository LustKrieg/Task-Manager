# Database for the Task Manager
import sqlite3
from datetime import datetime

DATABASE_NAME = "tasks.db"

# Function 0 -- Database connection
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
            created_at TEXT,
            deleted INTEGER DEFAULT 0,
            deleted_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Function 1.5 -- Database Migration
def migrate_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''PRAGMA table_info(tasks)''')
    columns = [column[1] for column in cursor.fetchall()]

    if "notes" not in columns:
        cursor.execute('''
            ALTER TABLE tasks
            ADD COLUMN notes TEXT
''')

    conn.commit()
    conn.close()

# Function 2 -- Add a new task to the database
def add_task(title):
    if not title.strip():
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    created_at = datetime.now().isoformat()
    
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
        SELECT id, title, completed, created_at FROM tasks
        WHERE completed = 0
        AND deleted = 0
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
        AND deleted = 0
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
    ''', (task_id,))

    conn.commit()
    conn.close()

# Function 6 -- Remove It Forever
def move_to_trash(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    deleted_at = datetime.now().isoformat()

    cursor.execute('''
        UPDATE tasks 
        SET deleted = 1,
            deleted_at = ?
        WHERE id = ?
    ''', (deleted_at, task_id))
    
    conn.commit()
    conn.close()

# Function 7 -- undo functionality for completed tasks
def mark_active(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE tasks
        SET completed = 0
        WHERE id = ?
    ''', (task_id,))

    conn.commit()
    conn.close()

create_table()
migrate_database()

# Function 8 -- editing an existing task
def update_task(task_id, new_title):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE tasks
    SET title = ?
    WHERE id = ?
''', (new_title, task_id))
    
    conn.commit()
    conn.close()

# Function 9 -- Deleting tasks to move to Deleted Recently
def get_deleted_tasks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM tasks
        WHERE deleted = 1
        ORDER BY deleted_at DESC
""")
    
    tasks = cursor.fetchall()
    conn.close()
    return tasks

# Function 10 -- Restore tasks from Recently Deleted
def restore_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE tasks
        SET deleted = 0,
        deleted_at = NULL
        WHERE id = ?
''', (task_id,))
    
    conn.commit()
    conn.close()

# Function 11 -- Delete task forever
def delete_forever(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM tasks
        WHERE id = ?
''', (task_id,))
    
    conn.commit()
    conn.close()

# Function 12 -- Empty Trash
def empty_trash():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM tasks
        WHERE deleted = 1
''')
    
    conn.commit()
    conn.close()

# Function 13 -- Update Task Notes
def update_notes(task_id, notes):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE tasks
        SET notes = ?
        WHERE id = ?
''', (notes, task_id))
    
    conn.commit()
    conn.close()

# Function 14 -- Get notes for a task
def get_notes(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT notes
        FROM tasks
        WHERE id = ?
''', (task_id,))
    
    result = cursor.fetchone()

    conn.close()

    if result and result[0] is not None:
        return result[0]
    return ""

