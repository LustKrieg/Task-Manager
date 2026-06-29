# Creating the Face of my Task-Manager
import database as db
import tkinter as tk
from tkmacosx import Button
from datetime import datetime

TASK_ROW_HEIGHT = 54

class TaskManagerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Task Manager")
        self.root.geometry("785x500")
        self.root.configure(bg="white")

        # ──────── Main Container ──────────────────────────────────────────────────
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

        content_frame = tk.Frame(main_container, bg="white")
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.section_title = tk.Label(
            content_frame,
            text="Active",
            font=("SF Pro Display", 28, "bold"),
            bg="white",
            fg="black"
        )
        self.section_title.pack(anchor="w", padx=20, pady=(20, 10))

        input_frame = tk.Frame(content_frame, bg="white")
        input_frame.pack(pady=20, padx=20, fill=tk.X)

        # ────── Sidebar buttons ─────────────────────────────────────────────────
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

        # ───── Scrollable task area ──────────────────────────────────────────────────────
        canvas = tk.Canvas(content_frame, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        self.task_frame = tk.Frame(canvas, bg="white")

        self.task_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window( (0, 0), window=self.task_frame, anchor="nw")

        def resize_frame(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", resize_frame)
        canvas.configure(yscrollcommand=scrollbar.set)

        self.root.bind_all("<MouseWheel>",
            lambda e:canvas.yview_scroll(-1 if e.delta > 0 else 1, "units"))

        self.root.bind_all("<Button-4>",
            lambda e: canvas.yview_scroll(-1, "units"))

        self.root.bind_all("<Button-5>",
            lambda e: canvas.yview_scroll(1, "units"))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ────────────── State ────────────────────────────────────────────────────
        self.current_view      = "active"
        self.selected_task_id  = None
        self.focus_job         = None
        self.highlighted_frame = None   # row currently highlighted by dbl-click
        self.pending_completion = {}

        # ────────────── Right-click context menu ──────────────────────────────────
        self.task_menu = tk.Menu(self.root, tearoff=0)
        self.task_menu.add_command(label="Delete",command=self.popup_delete_task)

        # Load active tasks by default
        self.load_tasks()

    # ════════════════════════════════════════════════════════════════════════
    #   PUBLIC
    # ════════════════════════════════════════════════════════════════════════
    def run(self):
        self.root.mainloop()

    # ════════════════════════════════════════════════════════════════════════
    #   NAVIGATION
    # ════════════════════════════════════════════════════════════════════════
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

    # ════════════════════════════════════════════════════════════════════════
    #   TASK CRUD HELPERS
    # ════════════════════════════════════════════════════════════════════════
    def add_task_from_entry(self, entry):
        title = entry.get()
        entry.delete(0, tk.END)
        self.add_task(title)

    def add_task(self, title):
        if title.strip():
            db.add_task(title)
            if self.current_view == "active":
                self.load_tasks()

    def complete_task(self, task_id):
        db.mark_complete(task_id)
        self.load_tasks()

    def undo_task(self, task_id):
        db.mark_active(task_id)
        self.load_tasks()

    def delete_task(self, task_id):
        db.delete_task(task_id)
        self.load_tasks()

    def popup_delete_task(self):
        db.delete_task(self.selected_task_id)
        self.load_tasks()

    def animate_complete(self, button, task_id):

        if task_id in self.pending_completion:
            job = self.pending_completion.pop(task_id)

            self.root.after_cancel(job)

            button.configure(text="○", fg="#8E8E93")
            return
        
        button.configure(text="◉",fg="#E30000")

        job = self.root.after(3000, lambda: self.finish_complete(task_id))
        self.pending_completion[task_id] = job

    def finish_complete(self, task_id):
        self.pending_completion.pop(task_id, None)
        self.complete_task(task_id)

    # ════════════════════════════════════════════════════════════════════════
    #   RIGHT-CLICK  FIX – 4
    # ════════════════════════════════════════════════════════════════════════
    def bind_right_click(self, widget, tid):
        def handler(event):
            self.selected_task_id = tid
            self.task_menu.tk_popup(event.x_root, event.y_root)
            self.task_menu.grab_release()

        widget.bind("<Button-3>", handler)
        widget.bind("<Button-2>", handler)      # macOS two-finger / right-click

    def _bind_rc_deep(self, widget, tid):   # recursively bind right-click on widget and all its descendants
        self.bind_right_click(widget, tid)
        for child in widget.winfo_children():
            self._bind_rc_deep(child, tid)

    # ════════════════════════════════════════════════════════════════════════
    #   LOAD / RENDER TASKS
    # ════════════════════════════════════════════════════════════════════════
    def load_tasks(self):
        self.current_edit = None
        # Clear existing tasks
        for widget in self.task_frame.winfo_children():
            widget.destroy()

        # ── "New Reminder" entry row ────────────────────────────────────────
        new_task_container = tk.Frame(self.task_frame,bg="white")
        new_task_container.pack(fill=tk.X, pady=5)
        circle = tk.Label(
            new_task_container,
            text="○",
            font=("SF PRo Text", 18),
            bg="white",
            fg="#8E8E93"
        )

        circle.pack(side=tk.RIGHT, padx=10)

        empty_task = tk.Entry(
            new_task_container,
            font=("SF PRo Text", 14),
            bg="white",
            fg="black",
            borderwidth=0,          # Removes the standard 3D box border
            highlightthickness=0,   # Removes the macOS blue focus ring/box border
            relief=tk.FLAT          # flattens the input widget completely
        )

        empty_task.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Frame(self.task_frame, bg="#D1D1D6", height=1).pack(fill=tk.X, pady=5)

        empty_task.bind("<Return>",lambda e: self.add_task_from_entry(empty_task))

        def set_placeholder(entry):
            entry.insert(0, "New Reminder")
            entry.config(fg="#8E8E93")

        set_placeholder(empty_task)

        def clear_placeholder(event):
            if event.widget.get() == "New Reminder":
                event.widget.delete(0, tk.END)
                event.widget.config(fg="black")

        def on_focus_out(event):
            if event.widget.get().strip() =="":
                event.widget.insert(0, "New Reminder")
                event.widget.config(fg="#8E8E93")

        empty_task.bind("<FocusIn>", clear_placeholder)
        empty_task.bind("<FocusOut>", on_focus_out)

        # ── Fetch tasks ─────────────────────────────────────────────────────
        tasks = db.get_active_tasks() if self.current_view == "active" else db.get_completed_tasks()

        # Display each task
        for task in tasks:
            task_id, title, completed, created_at  = task[0], task[1], task[2], task[3]

            try:                                                              # Format date/time (from "2025.10.21 14:30" to "Oct 21, 2:30 PM")
                dt = datetime.fromisoformat(created_at)
                date_str = dt.strftime('%b %d, %I:%M %p')
            except ValueError:                                                # Handle cases where the date format in the DB might be wrong
                date_str = f"Date Error: {created_at}"
            except Exception as e:
                date_str = f"Error: {e}"

            # ── Row container  ───────────────────────────────────────────────
            task_container = tk.Frame(
                self.task_frame,
                bg="white",
                height=TASK_ROW_HEIGHT             # fixed height, the row never jumps when we smap Label -> Entry
            )
            task_container.pack(fill=tk.X, pady=5)
            task_container.pack_propagate(False)
            
            text_container = tk.Frame(task_container, bg="white")
            text_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

            title_container = tk.Frame(text_container, bg="white", height=22)
            title_container.pack(fill=tk.X)

            # Task label
            text_color = "black" if not completed else "#8E8E93"
            
            task_label = tk.Label(
                title_container,
                text=title,
                font=("SF Pro Text", 14),
                fg=text_color,
                bg="white",
                anchor="w",
                bd=0,
                highlightthickness=0
            )
            task_label.grid(row=0, column=0, sticky="w")
            title_container.columnconfigure(0, weight=1)

            if not completed:                  # adjusted indentation for proper nesting within the code blocks
                task_label.bind(               # if not 4 indented spaces, all tasks would be as one in both sections
                    "<Button-1>",              # as of now, that change with "if not completed:" prohinits editing in completed tab
                    lambda e,
                    tid=task_id,
                    label=task_label:
                    self.edit_task(tid, label.cget("text"), label)
                )

            # Date/time label
            date_label = tk.Label(
                text_container,
                text=date_str,
                font=("SF Pro Text", 10),
                fg="#8E8E93",
                bg="white",
                anchor="w",
                highlightthickness=0
            )
            date_label.pack(anchor="w")

            # Buttons on right side
            # Complete button (only for active tasks)

            # ── Completion circle ────────────────────────────────────────────
            circle_btn = tk.Label(
                task_container,
                text="○" if not completed else "◉",
                font=("SF Pro Text", 18),
                bg="white",
                fg="#8E8E93" if not completed else "#E30000"
            )
            circle_btn.pack(side=tk.RIGHT, padx=10)

            # ACTIVE TASKS
            if not completed:
                circle_btn.bind("<Enter>", lambda e, btn=circle_btn: btn.configure(fg="#E30000"))
                circle_btn.bind("<Leave>", lambda e, btn=circle_btn, tid=task_id: btn.configure(fg="#E30000" if tid in self.pending_completion else "#8E8E93"))
                circle_btn.bind("<ButtonPress-1>", lambda e, b=circle_btn: b.configure(text="◉", fg="#8E8E93"))
                circle_btn.bind("<ButtonRelease-1>", lambda e, tid=task_id, btn=circle_btn: self.animate_complete(btn, tid))

            # COMPLETED TASKS
            else:
                circle_btn.bind("<Enter>", lambda e, btn=circle_btn: btn.configure(fg="#8E8E93"))
                circle_btn.bind("<Leave>", lambda e, btn=circle_btn:btn.configure(fg="#E30000"))
                circle_btn.bind("<ButtonPress-1>", lambda e, btn=circle_btn: btn.configure(text="◉", fg="#8E8E93"))
                circle_btn.bind("<ButtonRelease-1>", lambda e, tid=task_id, btn=circle_btn: self.undo_task(tid))

            # ── Single-click → inline edit  (active tasks only) ──────────────
            if not completed:
                for w in (task_label, title_container):
                    w.bind(
                        "<Button-1>",
                        lambda e, tid=task_id, lbl=task_label: 
                        self.edit_task(tid, lbl.cget("text"), lbl),
                    )

            # ────────────── Highlight row ───────────────────────────────────────────────────────
            self._bind_rc_deep(task_container, task_id)
            tk.Frame(self.task_frame, bg="#D1D1D6", height=1).pack(fill=tk.X, pady=5)

    # ════════════════════════════════════════════════════════════════════════
    #   DETAIL POPUP
    # ════════════════════════════════════════════════════════════════════════
    # for future development right-click pop-up window same as double trackpad click for delete button.
    # I don't want the window to be apart from the main window, just a nice popup as delete function.
    # ════════════════════════════════════════════════════════════════════════
    #   ROW BACKGROUND COLOR
    # ════════════════════════════════════════════════════════════════════════

    # ════════════════════════════════════════════════════════════════════════
    #   INLINE EDIT
    # ════════════════════════════════════════════════════════════════════════
    def edit_task(self, task_id, current_title, label_widget):
        if self.current_edit and self.current_edit[2] == task_id:
            return

        self.finish_edit(save=True)
        
        parent = label_widget.master

        edit_entry = tk.Entry(
            parent,
            font=("SF Pro Text", 14),
            bg="white",
            fg="black",
            borderwidth=0,
            highlightthickness=0,
            relief=tk.FLAT,
            insertbackground="#007AFF"
        )
        edit_entry.focus_set()
        edit_entry.insert(0, current_title)
        edit_entry.icursor(tk.END)
        edit_entry.configure(
            highlightthickness=0,
            bd=0,
            relief="flat",
            justify="left"
        )
        edit_entry.grid_configure(pady=(1, 0))

        edit_entry.grid(row=0, column=0, sticky="ew")
        parent.update_idletasks()

        edit_entry.bind("<FocusOut>", lambda e: self.finish_edit(save=True))
        edit_entry.bind("<Return>", lambda e: self.finish_edit(save=True))
        edit_entry.bind("<Escape>", lambda e: self.finish_edit(save=False))

        self.current_edit = (edit_entry, label_widget, task_id, current_title)

    def finish_edit(self, save=False, _skip_unbind=False):
        if not self.current_edit:
            return
        if self.focus_job:
            self.root.after_cancel(self.focus_job)
            self.focus_job = None

        entry, label, task_id, old_title = self.current_edit

        final_title = old_title

        if save:
            typed = entry.get().strip()

            if typed:
                final_title = typed

                if typed != old_title:
                    db.update_task(task_id, typed)

        if entry.winfo_exists():
            entry.grid_forget()
            entry.destroy()

        label.config(text=final_title)

        self.current_edit = None

#────────────── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = TaskManagerApp()
    app.run()
