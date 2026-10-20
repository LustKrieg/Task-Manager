import sqlite3
from pathlib import Path
from typing import List
from models import Task
from datetime import datetime

class TaskDatabase:
    def __init__(self, db_path: str = "tasks.db"):
        database_path = Path(db_path)
        if not database_path.is_absolute():
            database_path = Path(__file__).resolve().parent / database_path
        self.db_path = str(database_path)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

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
                ("notified_for_due_at", "TEXT"),
                ("modified_at", "TEXT"),
                ("priority", "INTEGER DEFAULT 0"),
                ("flagged", "INTEGER DEFAULT 0"),
            ):
                try:
                    conn.execute(f"ALTER TABLE tasks ADD COLUMN {column} {definition}")
                except sqlite3.OperationalError as error:
                    if "duplicate column name" not in str(error):
                        raise
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ai_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id)
                        REFERENCES ai_conversations (id) ON DELETE CASCADE
                )
            ''')

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

    def get_due_notification_candidates(self, now=None) -> List[Task]:
        now = now or datetime.now()
        with self._connect() as conn:
            rows = conn.execute('''
                SELECT id, title, completed, created_at, deleted, notes, due_at,
                       modified_at, priority, flagged, notified_for_due_at
                FROM tasks
                WHERE completed = 0 AND deleted = 0 AND due_at IS NOT NULL
            ''').fetchall()

        candidates = []
        for row in rows:
            due_at = self._to_datetime(row[6])
            if due_at.tzinfo is not None and now.tzinfo is None:
                comparison_now = now.astimezone(due_at.tzinfo)
            elif due_at.tzinfo is None and now.tzinfo is not None:
                comparison_now = now.astimezone().replace(tzinfo=None)
            else:
                comparison_now = now

            if due_at <= comparison_now and row[10] != row[6]:
                candidates.append(self._to_task(row[:10]))
        return candidates

    def mark_due_notification_sent(self, task_id: int, due_at: datetime) -> None:
        due_at_text = due_at.isoformat()
        with self._connect() as conn:
            conn.execute('''
                UPDATE tasks
                SET notified_for_due_at = ?
                WHERE id = ? AND due_at = ? AND completed = 0 AND deleted = 0
            ''', (due_at_text, task_id, due_at_text))
        
    def add_task(self, title: str, notes: str = "", due_at: datetime | None = None) -> bool:
        if not title.strip():
            return False
    
        created_at = datetime.now().isoformat()

        with self._connect() as conn:
            conn.execute('''
                                INSERT INTO tasks (title, notes, due_at, completed, deleted, created_at, modified_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (title.strip(), notes, due_at.isoformat() if due_at else None,
                                    0, 0, created_at, created_at))
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
            SET due_at = ?, notified_for_due_at = NULL, modified_at = ?
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

    def create_chat_conversation(self) -> int:
        created_at = datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            cursor = conn.execute('''
                INSERT INTO ai_conversations (title, created_at, updated_at)
                VALUES ('', ?, ?)
            ''', (created_at, created_at))
            return cursor.lastrowid

    def get_chat_conversations(self):
        with self._connect() as conn:
            rows = conn.execute('''
                SELECT id, title, created_at, updated_at
                FROM ai_conversations
                ORDER BY updated_at DESC, id DESC
            ''').fetchall()
        return [
            {"id": row[0], "title": row[1], "created_at": row[2], "updated_at": row[3]}
            for row in rows
        ]

    def get_chat_messages(self, conversation_id: int):
        with self._connect() as conn:
            rows = conn.execute('''
                SELECT id, role, content, created_at
                FROM ai_messages
                WHERE conversation_id = ?
                ORDER BY id
            ''', (conversation_id,)).fetchall()
        return [
            {"id": row[0], "role": row[1], "content": row[2], "created_at": row[3]}
            for row in rows
        ]

    def add_chat_message(self, conversation_id: int, content: str, role: str = "user") -> None:
        content = content.strip()
        if not content:
            return
        if role not in ("user", "assistant"):
            raise ValueError("Chat message role must be user or assistant")

        created_at = datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT title FROM ai_conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
            if row is None:
                raise ValueError("Chat conversation does not exist")

            conn.execute('''
                INSERT INTO ai_messages (conversation_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
            ''', (conversation_id, role, content, created_at))

            title = row[0]
            if not title and role == "user":
                title = content.splitlines()[0][:48]
            conn.execute('''
                UPDATE ai_conversations
                SET title = ?, updated_at = ?
                WHERE id = ?
            ''', (title, created_at, conversation_id))

    def delete_chat_conversation(self, conversation_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM ai_conversations WHERE id = ?", (conversation_id,))

    def update_chat_conversation_title(self, conversation_id: int, title: str) -> None:
        title = title.strip()
        with self._connect() as conn:
            conn.execute(
                "UPDATE ai_conversations SET title = ? WHERE id = ?",
                (title, conversation_id),
            )