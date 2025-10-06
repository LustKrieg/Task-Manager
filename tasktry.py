import tkinter as tk

root = tk.Tk()
root.title("Text Widget Example")

# Create a Text widget
text_widget = tk.Text(root, height=5, width=40, wrap="word") # wrap="word" ensures words wrap at the end of the line
text_widget.pack(pady=10)

# Insert initial text
text_widget.insert("1.0", "This is some initial text in the Text widget.\nYou can type more here.")

def get_text_content():
    content = text_widget.get("1.0", "end-1c") # "1.0" is line 1, character 0; "end-1c" gets all content except the final newline
    print(f"Text widget content:\n{content}")

button = tk.Button(root, text="Get Content", command=get_text_content)
button.pack()

root.mainloop()
