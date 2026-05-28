# Creating the Face of my Task-Manager
import database as db
import tkinter as tk
from tkmacosx import Button
from datetime import datetime

class TaskManagerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Task Manager")
        self.root.geometry("785x500")
        self.root.configure(bg="white")

        #Main Container
        main_container = tk.Frame(self.root, bg="white")
        main_container.pack(fill=tk.BOTH, expand=True)

        sidebar_frame = tk.Frame(
            main_container,
            bg="#E5E5EA",
            bd=2,
            width=280
        )
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        sidebar_frame.pack_propagate(False)

        #Content area
        content_frame = tk.Frame(
            main_container, bg="white"
        )
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.section_title = tk.Label(
            content_frame,
            text="Active",
            font=("SF Pro Display", 28, "bold"),
            bg="white",
            fg="black"
        )
        self.section_title.pack(anchor="w", padx=20, pady=(20, 10))

        # Input frame at top
        input_frame = tk.Frame(content_frame, bg="white")
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

        self.task_entry.bind(
            "<Return>",
            lambda e: self.add_task()
        )

        # Add button
        self.add_button = Button(
            input_frame,
            text="+",
            font=("SF Pro Text", 20),
            bg="white",
            fg="#8E8E93",
            borderless=1,
            activebackground="#E5E5EA",
            focuscolor="",
            borderwidth=0,
            highlightthickness=0,
            width=50,
            height=40,
            command=self.add_task
        )
        self.add_button.pack(side=tk.LEFT, padx=(10, 0))

        self.add_button.bind(
            "<Enter>",
            lambda e: self.add_button.configure(bg="#E5E5EA")
        )

        self.add_button.bind(
            "<Leave>",
            lambda e: self.add_button.configure(bg="white")
        )

        # Tab buttons frame
        tab_frame = tk.Frame(self.root, bg="white")
        tab_frame.pack(pady=(0, 10), padx=20, fill=tk.X)

        # Active tasks tab button
        self.active_tab_btn = Button(
            sidebar_frame,
            text="Active",
            font=("SF Pro Text", 14),
            bg="#D1D1D6",
            fg="black",
            borderless=1,
            activebackground="#E5E5EA",
            focuscolor="",
            width=130,
            height=60,
            command=self.show_active_tasks
        )
        self.active_tab_btn.pack(anchor="w", pady=5, padx=10)

        # Completed tasks tab button
        self.completed_tab_btn = Button(
            sidebar_frame,
            text="Completed",
            font=("SF Pro Text", 14),
            bg="#E5E5EA",
            fg="black",
            borderless=1,
            activebackground="#E5E5EA",
            focuscolor="",
            width=130,
            height=60,
            command=self.show_completed_tasks
        )
        self.completed_tab_btn.pack(anchor="w", pady=5, padx=10)

        # Scrollable frame for tasks
        canvas = tk.Canvas(content_frame, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
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

        # Right click popup menu
        self.task_menu = tk.Menu(self.root, tearoff=0)
        self.task_menu.add_command(label="Delete",command=self.popup_delete_task)

        self.selected_task_id = None

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
        self.active_tab_btn.configure(bg="#D1D1D6", fg="white")
        self.completed_tab_btn.configure(bg="#E5E5EA", fg="black")
        self.section_title.configure(text="Active")
        self.load_tasks()

    def show_completed_tasks(self):
        self.current_view = "completed"
        # Update button styles
        self.section_title.configure(text="Completed")
        self.active_tab_btn.configure(bg="#E5E5EA", fg="black")
        self.completed_tab_btn.configure(bg="#D1D1D6", fg="white")
        self.load_tasks()



    # RIGHT CLICK SYSTEM
    def bind_right_click(self, widget, tid):
        def handler(event):
            self.selected_task_id = tid
            self.task_menu.tk_popup(event.x_root, event.y_root)
            self.task_menu.grab_release()

        widget.bind("<Button-3>", handler)
        widget.bind("<Button-2>", handler)  # mac support

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
            # We will use color change for simplicity:
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
            # Complete button (only for active tasks)
    # Completion circle
            circle_btn = tk.Label(
                task_container,
                text="○" if not completed else "◉",
                font=("SF Pro Text", 18),
                bg="white",
                fg="#8E8E93"
            )

            circle_btn.pack(side=tk.RIGHT, padx=10)

            # Hover enter
            circle_btn.bind(
                "<Enter>",
                lambda e, btn=circle_btn:
                    btn.configure(fg="#D30000")
            )

            # Hover leave
            circle_btn.bind(
                "<Leave>",
                lambda e, btn=circle_btn:
                    btn.configure(
                        fg="#8E8E93" if btn.cget("text") == "○"
                        else "#D30000"
                    )
            )

            # Mouse press
            circle_btn.bind(
                "<ButtonPress-1>",
                lambda e, btn=circle_btn:
                    btn.configure(fg="gray")
            )

            # ACTIVE TASKS
            if not completed:
                circle_btn.bind(
                    "<Button-1>",
                    lambda e, tid=task_id, btn=circle_btn:
                        self.animate_complete(btn, tid)
                )

            # COMPLETED TASKS
            else:
                circle_btn.bind(
                    "<Button-1>",
                    lambda e, tid=task_id:
                        self.undo_task(tid)
                )

            # right click ON ALL elements
            for w in (task_container, text_container, task_label, date_label, circle_btn):
                self.bind_right_click(w, task_id)

            separator = tk.Frame(
                self.task_frame,
                bg="#D1D1D6",
                height=1
            )
            separator.pack(fill=tk.X, padx=10, pady=5)

    def complete_task(self, task_id):
        db.mark_complete(task_id)
        self.load_tasks()

    def undo_task(self, task_id):
        db.mark_active(task_id)
        self.load_tasks()

    def show_task_menu(self, event, task_id):
        self.selected_task_id = task_id
        self.task_menu.tk_popup(event.x_root, event.y_root)
        self.task_menu.grab_release()

    def popup_delete_task(self):
        db.delete_task(self.selected_task_id)
        self.load_tasks()

    def animate_complete(self, button, task_id):
        button.configure(text="◉", fg="#D30000")
        self.root.after(250,lambda: self.complete_task(task_id))

    def delete_task(self, task_id):
        db.delete_task(task_id)
        self.load_tasks()


# Run app directly
if __name__ == "__main__":
    app = TaskManagerApp()
    app.run()
