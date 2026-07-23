import sqlite3
from typing import List
from models import Task
from datetime import datetime

class TaskDatabase:
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def get_active(self) -> List[Task]:
        with self._connect() as conn:
            cursor = conn.execute('''
                SELECT id, title, completed, created_at, deleted, notes
                FROM tasks WHERE completed = 0 AND deleted = 0
                ORDER BY created_at DESC
            ''')

            rows = cursor.fetchall()

            return [Task(
                id=row[0],
                title=row[1],
                completed=row[2],
                created_at=datetime.fromisoformat(row[3]),
                deleted=row[4],
                notes=row[5] if row[5] else ""
            ) for row in rows]
        
    def add_task(self, title: str, notes: str = "") -> bool:
        if not title.strip():
            return False
    
        created_at = datetime.now().isoformat()

        with self._connect() as conn:
            conn.execute('''
                INSERT INTO tasks (title, notes, completed, deleted, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (title.strip(), notes, 0, 0, created_at))
            return True

    def mark_complete(self, task_id: int) -> None:
        with self._connect() as conn:
            conn.execute('''
            UPDATE tasks 
            SET completed = 1 
            WHERE id = ?
            ''', 
            (task_id,)
        )

    def undo_task(self, task_id: int) -> None:
        with self._connect() as conn:
            conn.execute('''
            UPDATE tasks 
                SET completed = 0 
                WHERE id =?
                ''',
                (task_id,)
            )
    