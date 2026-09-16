import tkinter as tk
from wiki_generator import generate_creator_wiki

def run_app(creators, merged_data):
    root = tk.Tk()
    root.title("Creator Activity Viewer")

    left_frame = tk.Frame(root)
    left_frame.pack(side="left", fill="y")

    right_frame = tk.Frame(root)
    right_frame.pack(side="right", fill="both", expand=True)

    # Text box for wiki output
    wiki_box = tk.Text(right_frame, wrap="word")
    wiki_box.pack(fill="both", expand=True)

    # Copy button
    copy_btn = tk.Button(right_frame, text="Copy Wiki Code", command=lambda: copy_to_clipboard(wiki_box))
    copy_btn.pack(fill="x")

    def on_creator_click(creator):
        wiki = generate_creator_wiki(merged_data, creator)
        wiki_box.delete("1.0", "end")
        wiki_box.insert("1.0", wiki)

    build_creator_buttons(left_frame, creators, on_creator_click)

    root.mainloop()


def build_creator_buttons(frame, creators, callback):
    for creator in creators:
        btn = tk.Button(
            frame,
            text=creator,
            command=lambda c=creator: callback(c)
        )
        btn.pack(fill="x")


def copy_to_clipboard(widget):
    text = widget.get("1.0", "end")
    widget.clipboard_clear()
    widget.clipboard_append(text)
