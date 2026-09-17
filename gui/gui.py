import tkinter as tk
from tkinter import filedialog, ttk
import csv
from collections import defaultdict
from wiki_generator import generate_creator_wiki, generate_day_block

def run_app(creators, merged_data, vod_mismatches=None):
    root = tk.Tk()
    root.title("QSMP Wiki Helper")
    root.geometry("900x600")

    header = tk.Frame(root)
    header.pack(fill="x")

    info_button = tk.Button(header, text="i", width=3, cursor="question_arrow")
    info_button.pack(side="right", padx=8, pady=6)
    add_tooltip(
        info_button,
        "Lore Templates creates month or day wiki templates.\n"
        "Timeline Mismatch lists VOD entries missing from the activity spreadsheet.\n"
        "The third tab is reserved for a future feature."
    )

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    lore_tab = ttk.Frame(notebook)
    mismatch_tab = ttk.Frame(notebook)
    empty_tab = ttk.Frame(notebook)
    notebook.add(lore_tab, text="Lore Templates")
    notebook.add(mismatch_tab, text="Timeline Mismatch")
    notebook.add(empty_tab, text="Coming Later")

    left_frame = tk.Frame(lore_tab)
    left_frame.pack(side="left", fill="y", padx=8, pady=8)

    right_frame = tk.Frame(lore_tab)
    right_frame.pack(side="right", fill="both", expand=True, padx=(0, 8), pady=8)

    selected_creator = tk.StringVar()
    selected_day = tk.StringVar()
    day_entries = {}

    day_label = tk.Label(left_frame, text="Day template")
    day_label.pack(fill="x", pady=(8, 0))

    day_menu = ttk.Combobox(left_frame, textvariable=selected_day, state="readonly")
    day_menu.pack(fill="x")

    def generate_selected_day():
        entry = day_entries.get(selected_day.get())
        if entry is None:
            return

        wiki_box.delete("1.0", "end")
        wiki_box.insert("1.0", generate_day_block(entry))

    day_btn = tk.Button(
        left_frame,
        text="Generate Day Template",
        command=generate_selected_day
    )
    day_btn.pack(fill="x", pady=(4, 8))

    creator_list_frame = tk.Frame(left_frame)
    creator_list_frame.pack(fill="both", expand=True)

    creator_canvas = tk.Canvas(creator_list_frame, width=180, highlightthickness=0)
    creator_scrollbar = ttk.Scrollbar(
        creator_list_frame,
        orient="vertical",
        command=creator_canvas.yview
    )
    creator_buttons_frame = tk.Frame(creator_canvas)
    creator_canvas_window = creator_canvas.create_window(
        (0, 0),
        window=creator_buttons_frame,
        anchor="nw"
    )
    creator_canvas.configure(yscrollcommand=creator_scrollbar.set)
    creator_canvas.pack(side="left", fill="both", expand=True)
    creator_scrollbar.pack(side="right", fill="y")

    def update_creator_scroll_region(_event=None):
        creator_canvas.configure(scrollregion=creator_canvas.bbox("all"))

    def resize_creator_buttons(event):
        creator_canvas.itemconfigure(creator_canvas_window, width=event.width)

    creator_buttons_frame.bind("<Configure>", update_creator_scroll_region)
    creator_canvas.bind("<Configure>", resize_creator_buttons)

    # Text box for wiki output
    wiki_box = tk.Text(right_frame, wrap="word")
    wiki_box.pack(fill="both", expand=True)

    # Copy button
    copy_btn = tk.Button(right_frame, text="Copy Wiki Code", command=lambda: copy_to_clipboard(wiki_box))
    copy_btn.pack(fill="x")

    def on_creator_click(creator):
        selected_creator.set(creator)
        day_entries.clear()

        for entry in merged_data.get(creator, []):
            label = f"Day {entry['server_day']} - {entry['wiki_date']}"
            day_entries[label] = entry

        day_menu["values"] = list(day_entries)
        selected_day.set("")

        wiki = generate_creator_wiki(merged_data, creator)
        wiki_box.delete("1.0", "end")
        wiki_box.insert("1.0", wiki)

    build_creator_buttons(creator_buttons_frame, creators, on_creator_click)

    build_mismatch_view(mismatch_tab, vod_mismatches or [])

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


def build_mismatch_view(frame, mismatches):
    heading = tk.Label(
        frame,
        text="Show creators not listed in Timeline Tracking spreadsheet but have VODs in the VOD spreadsheet.",
        anchor="w"
    )
    heading.pack(fill="x", padx=12, pady=(12, 6))

    save_button = tk.Button(
        frame,
        text="Save Findings",
        command=lambda: save_mismatches(mismatches)
    )
    save_button.pack(anchor="w", padx=12, pady=(0, 8))

    selected_mismatch = {"value": None}

    def copy_selected_vod():
        mismatch = selected_mismatch["value"]
        if mismatch is None:
            return

        frame.clipboard_clear()
        frame.clipboard_append(mismatch["vod"])

    copy_button = tk.Button(
        frame,
        text="Copy VOD Link",
        command=copy_selected_vod
    )
    copy_button.pack(anchor="w", padx=12, pady=(0, 8))

    table = ttk.Treeview(frame, columns=("vod",), show="tree headings")
    table.heading("#0", text="Date / Creator")
    table.heading("vod", text="VOD")
    table.column("#0", width=300, anchor="w")
    table.column("vod", width=500, anchor="w")
    table.tag_configure("non_qsmp", foreground="#d97706")

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scrollbar.set)
    table.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 12))
    scrollbar.pack(side="right", fill="y", padx=(0, 12), pady=(0, 12))

    findings_by_date = defaultdict(list)
    for mismatch in mismatches:
        findings_by_date[mismatch["calendar_day"]].append(mismatch)

    for date, date_findings in sorted(findings_by_date.items()):
        date_item = table.insert("", "end", text=date, open=True)
        for mismatch in date_findings:
            title = mismatch.get("vod_title", "")
            tags = ("non_qsmp",) if "qsmp" not in title.lower() else ()
            item_id = table.insert(
                date_item,
                "end",
                text=mismatch["creator"],
                values=(mismatch["vod"],),
                tags=tags
            )
            table.item(item_id, tags=tags)

    def select_mismatch(_event):
        selection = table.selection()
        if not selection:
            return

        item_id = selection[0]
        if table.parent(item_id) == "":
            selected_mismatch["value"] = None
            return

        creator = table.item(item_id, "text")
        date = table.item(table.parent(item_id), "text")
        selected_mismatch["value"] = next(
            (
                mismatch for mismatch in mismatches
                if mismatch["creator"] == creator
                and mismatch["calendar_day"] == date
            ),
            None
        )

    table.bind("<<TreeviewSelect>>", select_mismatch)
    table.bind("<Double-1>", select_mismatch)


def save_mismatches(mismatches):
    file_path = filedialog.asksaveasfilename(
        title="Save Findings",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile="timeline_mismatches.csv"
    )
    if not file_path:
        return

    with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["Creator", "Date", "VOD Title", "VOD"])
        for mismatch in mismatches:
            writer.writerow([
                mismatch["creator"],
                mismatch["calendar_day"],
                mismatch.get("vod_title", ""),
                mismatch["vod"]
            ])


def add_tooltip(widget, text):
    tooltip = None

    def show_tooltip(_event):
        nonlocal tooltip
        if tooltip is not None:
            return

        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{widget.winfo_rootx() - 320}+{widget.winfo_rooty() + 30}")
        tk.Label(
            tooltip,
            text=text,
            justify="left",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=6,
            background="#fffde6"
        ).pack()

    def hide_tooltip(_event):
        nonlocal tooltip
        if tooltip is not None:
            tooltip.destroy()
            tooltip = None

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)
