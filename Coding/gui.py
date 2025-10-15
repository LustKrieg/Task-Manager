# Creating the Face of my Task-Manager
import database as db
import tkinter as tk
from tkmacosx import Button


class TaskManagerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Task Manager")
        self.root.geometry("400x600")
        self.root.configure(bg="white")

        # Input frame at top
        input_frame = tk.Frame(self.root, bg="white")
        input_frame.pack(pady=20, padx=20, fill=tk.X)

        # Text entry
        self.task_entry = tk.Entry(
            input_frame,
            font=("SF Pro Text", 16),
            bg="#F2F2F7",
            relief=tk.FLAT,
            borderwidth=10
        )
        self.task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Add button
        self.add_button = Button(
            input_frame,
            text="+",
            font=("SF Pro Text", 20),
            bg="#007AFF",
            fg="white",
            borderless=True,
            width=50,
            height=40,
            command=self.add_task
        )
        self.add_button.pack(side=tk.LEFT, padx=(10, 0))

        # Scrollable frame for tasks
        canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.task_frame = tk.Frame(canvas, bg="white")

        self.task_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.task_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ✅ load tasks AFTER creating the frame
        self.load_tasks()

    def run(self):
        self.root.mainloop()

    def add_task(self):
        """Add a new task when + button is clicked"""
        title = self.task_entry.get()

        if title.strip():  # Only if not empty
            db.add_task(title)
            self.task_entry.delete(0, tk.END)  # Clear input
            self.load_tasks()  # Refresh the list

    def load_tasks(self):
        """Load and display all active tasks"""
        # Clear existing tasks
        for widget in self.task_frame.winfo_children():
            widget.destroy()

        # Get tasks from database
        tasks = db.get_active_tasks()

        # Display each task
        for task in tasks:
            task_id, title = task

            # Task container
            task_container = tk.Frame(self.task_frame, bg="white")
            task_container.pack(fill=tk.X, pady=5)

            # Task text
            task_label = tk.Label(
                task_container,
                text=title,
                font=("SF Pro Text", 14),
                bg="white",
                anchor="w"
            )
            task_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Complete button
            complete_btn = Button(
                task_container,
                text="✓",
                font=("SF Pro Text", 16),
                bg="#34C759",
                fg="white",
                borderless=True,
                width=35,
                height=35,
                command=lambda tid=task_id: self.complete_task(tid)
            )
            complete_btn.pack(side=tk.RIGHT, padx=5)

            # Delete button
            delete_btn = Button(
                task_container,
                text="×",
                font=("SF Pro Text", 20),
                bg="#FF3B30",
                fg="white",
                borderless=True,
                width=35,
                height=35,
                command=lambda tid=task_id: self.delete_task(tid)
            )
            delete_btn.pack(side=tk.RIGHT)

    def complete_task(self, task_id):
        """Mark task as complete"""
        db.mark_complete(task_id)
        self.load_tasks()

    def delete_task(self, task_id):
        """Delete a task"""
        db.delete_task(task_id)
        self.load_tasks()


# ✅ Run app directly
if __name__ == "__main__":
    app = TaskManagerApp()
    app.run()

    