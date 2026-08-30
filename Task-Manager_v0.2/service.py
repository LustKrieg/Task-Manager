from database import TaskDatabase
from models import Task
from typing import List
from datetime import datetime

class TaskService:
    def __init__(self, db: TaskDatabase):
        self.db = db

    def get_active_tasks(self) -> List[Task]:
        return self.db.get_active()

    def get_completed_tasks(self) -> List[Task]:
        return self.db.get_completed()

    def get_deleted_tasks(self) -> List[Task]:
        return self.db.get_deleted()

    def add_task(self, title: str, notes: str = "") -> bool:
        if not title.strip():
            return False
        return self.db.add_task(title.strip(), notes)

    def complete_task(self, task_id: int) -> None:
        self.db.mark_complete(task_id)

    def undo_task(self, task_id: int) -> None:
        self.db.undo_task(task_id)

    def move_to_trash(self, task_id: int) -> None:
        self.db.move_to_trash(task_id)

    def restore_task(self, task_id: int) -> None:
        self.db.restore_task(task_id)

    def delete_forever(self, task_id: int) -> None:
        self.db.delete_forever(task_id)

    def update_notes(self, task_id: int, notes: str) -> None:
        self.db.update_notes(task_id, notes)

    def update_task_title(self, task_id: int, new_title: str) -> None:
        if not new_title.strip():
            return
        self.db.update_task_title(task_id, new_title.strip())

    def update_due_at(self, task_id: int, due_at: datetime | None) -> None:
        self.db.update_due_at(task_id, due_at)

    def update_priority(self, task_id: int, priority: int) -> None:
        self.db.update_priority(task_id, priority)

    def update_flagged(self, task_id: int, flagged: bool) -> None:
        self.db.update_flagged(task_id, flagged)

    def empty_trash(self):
        self.db.empty_trash()

    def restore_all(self) -> None:
        self.db.restore_all()

    def get_notes(self, task_id: int) -> str:
        return self.db.get_notes(task_id)

    def get_task(self, task_id: int) -> Task | None:
        return self.db.get_task(task_id)

if __name__ == "__main__":
    db = TaskDatabase()
    db.create_table()
    service = TaskService(db)
    print(f"Active tasks: {len(service.get_active_tasks())}")
    print("Service in ready to go!")
