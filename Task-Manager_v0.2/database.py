import sqlite3
from typing import List
from models import Task
from datetime import datetime

class TaskDatabase:
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def create_table(self) -> None:
        with self._connect() as conn:
            conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            created_at TEXT,
            deleted INTEGER DEFAULT 0,
            notes TEXT
            )
        ''')
            for column, definition in (
                ("due_at", "TEXT"),
                ("modified_at", "TEXT"),
                ("priority", "INTEGER DEFAULT 0"),
                ("flagged", "INTEGER DEFAULT 0"),
            ):
                try:
                    conn.execute(f"ALTER TABLE tasks ADD COLUMN {column} {definition}")
                except sqlite3.OperationalError as error:
                    if "duplicate column name" not in str(error):
                        raise

    @staticmethod
    def _to_datetime(value):
        return datetime.fromisoformat(value) if value else None

    @staticmethod
    def _to_task(row) -> Task:
        return Task(
            id=row[0], title=row[1], completed=bool(row[2]),
            created_at=datetime.fromisoformat(row[3]), deleted=bool(row[4]),
            notes=row[5] or "", due_at=TaskDatabase._to_datetime(row[6]),
            modified_at=TaskDatabase._to_datetime(row[7]), priority=row[8] or 0,
            flagged=bool(row[9]),
        )

    def get_active(self) -> List[Task]:
        with self._connect() as conn:
            cursor = conn.execute('''
                SELECT id, title, completed, created_at, deleted, notes, due_at, modified_at, priority, flagged
                FROM tasks WHERE completed = 0 AND deleted = 0
                ORDER BY created_at DESC
            ''')

            rows = cursor.fetchall()

            return [self._to_task(row) for row in rows]
        
    def add_task(self, title: str, notes: str = "") -> bool:
        if not title.strip():
            return False
    
        created_at = datetime.now().isoformat()

        with self._connect() as conn:
            conn.execute('''
                INSERT INTO tasks (title, notes, completed, deleted, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title.strip(), notes, 0, 0, created_at, created_at))
            return True

    def mark_complete(self, task_id: int) -> None:
        with self._connect() as conn:
            conn.execute('''
            UPDATE tasks
            SET completed = 1, modified_at = ?
            WHERE id = ?
            ''', (datetime.now().isoformat(), task_id))

    def undo_task(self, task_id: int) -> None:
        with self._connect() as conn:
            conn.execute('''
            UPDATE tasks
            SET completed = 0, modified_at = ?
            WHERE id =?
            ''', (datetime.now().isoformat(), task_id))

    def get_completed(self) -> List[Task]:
        with self._connect() as conn:
            rows = conn.execute('''
                SELECT id, title, completed, created_at, deleted, notes, due_at, modified_at, priority, flagged
                FROM tasks WHERE completed = 1 AND deleted = 0
                ORDER BY created_at DESC
            ''').fetchall()
            return [self._to_task(row) for row in rows]

    def get_deleted(self) -> List[Task]:
        with self._connect() as conn:
            rows = conn.execute('''
                SELECT id, title, completed, created_at, deleted, notes, due_at, modified_at, priority, flagged
                FROM tasks WHERE deleted = 1
                ORDER BY created_at DESC
            ''').fetchall()
            return [self._to_task(row) for row in rows]

    def move_to_trash(self, task_id: int) -> None:
        with self._connect() as conn:
            conn.execute('''
            UPDATE tasks
            SET deleted = 1, modified_at = ?
            WHERE id = ?
            ''', (datetime.now().isoformat(), task_id))

    def restore_task(self, task_id: int) -> None:
        with self._connect() as conn:
            conn.execute('''
            UPDATE tasks
            SET deleted = 0, modified_at = ?
            WHERE id = ?
            ''', (datetime.now().isoformat(), task_id))

    def delete_forever(self, task_id: int) -> None:
        with self._connect() as conn:
            conn.execute('''
            DELETE FROM tasks
            WHERE id = ?
            ''', (task_id,))

    def empty_trash(self) -> None:
        with self._connect() as conn:
            conn.execute('''
            DELETE FROM tasks
            WHERE deleted = 1
            ''')

    def update_notes(self, task_id: int, notes: str) -> None:
        with self._connect() as conn:
            conn.execute('''
            UPDATE tasks
            SET notes = ?, modified_at = ?
            WHERE id = ?
            ''', (notes, datetime.now().isoformat(), task_id))

    def update_task_title(self, task_id: int, new_title: str) -> None:
        with self._connect() as conn:
            conn.execute('''
            UPDATE tasks
            SET title = ?, modified_at = ?
            WHERE id = ?
            ''', (new_title.strip(), datetime.now().isoformat(), task_id))

    def update_due_at(self, task_id: int, due_at: datetime | None) -> None:
        with self._connect() as conn:
            conn.execute('''
            UPDATE tasks
            SET due_at = ?, modified_at = ?
            WHERE id = ?
            ''', (due_at.isoformat() if due_at else None, datetime.now().isoformat(), task_id))

    def update_priority(self, task_id: int, priority: int) -> None:
        with self._connect() as conn:
            conn.execute('''
            UPDATE tasks
            SET priority = ?, modified_at = ?
            WHERE id = ?
            ''', (priority, datetime.now().isoformat(), task_id))

    def update_flagged(self, task_id: int, flagged: bool) -> None:
        with self._connect() as conn:
            conn.execute('''
            UPDATE tasks
            SET flagged = ?, modified_at = ?
            WHERE id = ?
            ''', (int(flagged), datetime.now().isoformat(), task_id))

    def restore_all(self) -> None:
        with self._connect() as conn:
            conn.execute('''
            UPDATE tasks
            SET deleted = 0, modified_at = ?
            WHERE deleted = 1
            ''', (datetime.now().isoformat(),))

    def get_notes(self, task_id: int) -> str:
        with self._connect() as conn:
            result = conn.execute('''
            SELECT notes
            FROM tasks
            WHERE id = ?
            ''', (task_id,)).fetchone()
            return result[0] if result and result[0] else ""

    def get_task(self, task_id: int) -> Task | None:
        with self._connect() as conn:
            row = conn.execute('''
                SELECT id, title, completed, created_at, deleted, notes, due_at, modified_at, priority, flagged
                FROM tasks
                WHERE id = ?
            ''', (task_id,)).fetchone()

            if row is None:
                return None

            return self._to_task(row)