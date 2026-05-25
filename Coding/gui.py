# Creating the Face of my Task-Manager
import database as db
import tkinter as tk
from tkmacosx import Button
from datetime import datetime


class TaskManagerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Task Manager")
        self.root.geometry("600x800")
        self.root.configure(bg="white")

        # Input frame at top
        input_frame = tk.Frame(self.root, bg="white")
        input_frame.pack(pady=20, padx=20, fill=tk.X)

        # Text entry
        self.task_entry = tk.Entry(
            input_frame,
            font=("SF Pro Text", 16),
            bg="#F2F2F7",
            fg="black",
            insertbackground="black",
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

        # Tab buttons frame
        tab_frame = tk.Frame(self.root, bg="white")
        tab_frame.pack(pady=(0, 10), padx=20, fill=tk.X)

        # Active tasks tab button
        self.active_tab_btn = Button(
            tab_frame,
            text="Active",
            font=("SF Pro Text", 14),
            bg="#007AFF",
            fg="white",
            borderless=True,
            width=100,
            height=35,
            command=self.show_active_tasks
        )
        self.active_tab_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Completed tasks tab button
        self.completed_tab_btn = Button(
            tab_frame,
            text="Completed",
            font=("SF Pro Text", 14),
            bg="#E5E5EA",
            fg="black",
            borderless=True,
            width=100,
            height=35,
            command=self.show_completed_tasks
        )
        self.completed_tab_btn.pack(side=tk.LEFT)

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

        self.root.bind_all(
            "<MouseWheel>",
            lambda e:canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")
        )

        self.root.bind_all(
            "<Button-4>",
            lambda e: canvas.yview_scroll(-1, "units")
        )

        self.root.bind_all(
            "<Button-5>",
            lambda e: canvas.yview_scroll(1, "units")
        )

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Track current view
        self.current_view = "active"

        # Load active tasks by default
        self.load_tasks()

    def run(self):
        self.root.mainloop()

    def add_task(self):
        title = self.task_entry.get()

        if title.strip():
            db.add_task(title)
            self.task_entry.delete(0, tk.END)
            if self.current_view == "active":
                self.load_tasks()

    def show_active_tasks(self):
        self.current_view = "active"
        # Update button styles
        self.active_tab_btn.configure(bg="#007AFF", fg="white")
        self.completed_tab_btn.configure(bg="#E5E5EA", fg="black")
        self.load_tasks()

    def show_completed_tasks(self):
        self.current_view = "completed"
        # Update button styles
        self.active_tab_btn.configure(bg="#E5E5EA", fg="black")
        self.completed_tab_btn.configure(bg="#007AFF", fg="white")
        self.load_tasks()

    def load_tasks(self):
        # Clear existing tasks
        for widget in self.task_frame.winfo_children():
            widget.destroy()

        # Get tasks based on current view
        if self.current_view == "active":
            tasks = db.get_active_tasks()
        else:
            tasks = db.get_completed_tasks()

        # Display each task
        for task in tasks:
            task_id = task[0]
            title = task[1]
            completed = task[2]
            created_at = task[3]
            
            # Format date/time (from "2025.10.21 14:30" to "Oct 21, 2:30 PM")
            try:
                # Use the format string that matches how you saved it in database.py
                dt = datetime.fromisoformat(created_at)
                date_str = dt.strftime('%b %d, %I:%M %p')
            except ValueError:
                # Handle cases where the date format in the DB might be wrong
                date_str = f"Date Error: {created_at}"
            except Exception as e:
                date_str = f"An unexpected error occurred: {e}"

            # Task container
            task_container = tk.Frame(self.task_frame, bg="white")
            task_container.pack(fill=tk.X, pady=5)

            # Left side: task text and date
            text_container = tk.Frame(task_container, bg="white")
            text_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Task text (with strikethrough if completed)
            # Strikethrough display needs specific configuration/tags in standard Tkinter Label which is complex.
            # We will use color change for simplicity as you did:
            text_color = "black" if not completed else "#8E8E93"
            
            task_label = tk.Label(
                text_container,
                text=title,
                font=("SF Pro Text", 14),
                fg=text_color,
                bg="white",
                anchor="w"
            )
            task_label.pack(anchor="w")

            # Date/time label
            date_label = tk.Label(
                text_container,
                text=date_str,
                font=("SF Pro Text", 10),
                fg="#8E8E93",
                bg="white",
                anchor="w"
            )
            date_label.pack(anchor="w")

            # Buttons on right side
            if self.current_view == "active":
                # Complete button (only for active tasks)
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

            # Delete button (available in both views)
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


# Run app directly
if __name__ == "__main__":
    app = TaskManagerApp()
    app.run()
