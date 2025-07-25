
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Constants
SAVE_FILE = "ow2_stats.json"
HEROES_FILE = "heroes.json"
MATCH_LOG_FILE = "match_log.json"
DARK_BG = "#06141B"
MID_BG = "#11212D"
LIGHT_BG = "#253745"
FONT_COLOR = "#ffffff"
MODERN_FONT = ("Segoe UI", 10)
# Directory containing the hero icon images.  The icons are bundled with the
# project inside the ``hero_icons`` folder, so build the path relative to this
# file to ensure it works regardless of where the script is run from.
ICON_DIR = os.path.join(os.path.dirname(__file__), "hero_icons")

# Globals
match_log = []
if os.path.exists(MATCH_LOG_FILE):
    with open(MATCH_LOG_FILE, "r", encoding="utf-8") as f:
        match_log = json.load(f)

if os.path.exists(HEROES_FILE):
    with open(HEROES_FILE, "r") as f:
        HEROES_BY_ROLE = json.load(f)
else:
    HEROES_BY_ROLE = {
        "Tank": ["D.Va", "Doomfist", "Orisa"],
        "Damage": ["Cassidy", "Sojourn", "Reaper"],
        "Support": ["Ana", "Moira", "Kiriko"]
    }

def animate_highlight(canvas, rect, start, end, steps=10, delay=10, anim_flag=None):
    if anim_flag is not None and anim_flag["running"]:
        return
    if anim_flag is not None:
        anim_flag["running"] = True

    delta = (end - start) / steps
    def step(i=0):
        if i > steps:
            if anim_flag is not None:
                anim_flag["running"] = False
            return
        canvas.coords(rect, 0, 0, start + delta * i, 30)
        canvas.after(delay, step, i + 1)
    step()

    with open(HEROES_FILE, "w") as f:
        json.dump(HEROES_BY_ROLE, f)

ALL_HEROES = {h.lower(): role for role, heroes in HEROES_BY_ROLE.items() for h in heroes}
MAPS = ['New Queen Street', 'Colosseo', 'Esperança', 'New Junk City', 'Circuit Royal', 'Dorado', 'Havana', 'Junkertown', 'Route 66', 'Shambali Monastery', 'Blizzard World', 'Eichenwalde', 'King’s Row', 'Midtown', 'Numbani', 'Paraíso', 'Ilios', 'Lijiang Tower', 'Nepal', 'Oasis', 'Antarctic Peninsula', 'Samoa', 'Suravasa']

if os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "r") as f:
        data = json.load(f)
        teammate_matches = data.get("teammates", {})
        enemy_matches = data.get("enemies", {})
        total_matches = data.get("matches", 0)
        map_stats = data.get("map_stats", {})
else:
    teammate_matches, enemy_matches, total_matches, map_stats = {}, {}, 0, {}

def save_data():
    with open(SAVE_FILE, "w") as f:
        json.dump({
            "teammates": teammate_matches,
            "enemies": enemy_matches,
            "matches": total_matches,
            "map_stats": map_stats
        }, f)

def display_stats(teammate_tree, enemy_tree):
    def fill_tree(tree, data):
        tree.delete(*tree.get_children())
        if total_matches:
            sorted_data = sorted(
                [(h.title(), f"{(c / total_matches) * 100:.2f}%", c) for h, c in data.items()],
                key=lambda x: -x[2],
            )
        else:
            sorted_data = []
        for row in sorted_data:
            tree.insert("", "end", values=row)

    fill_tree(teammate_tree, teammate_matches)
    fill_tree(enemy_tree, enemy_matches)

ICON_CACHE = {}  # add this near top of your file, after constants

class ScrollableIconMenu(tk.Frame):
    """A custom dropdown widget that displays hero icons with a scrollable list."""

    def __init__(self, parent, values, variable):
        super().__init__(parent, bg=DARK_BG)
        self.values = values
        self.variable = variable

        # Determine a sensible width for the button based on the longest hero
        # name provided.  "2" extra characters keeps things from feeling
        # cramped but avoids the excessive padding the old fixed width added.
        max_len = max((len(h) for h in values), default=0) + 2
        self.button = tk.Button(
            self,
            textvariable=self.variable,
            width=max_len,
            relief="raised",
            bg=LIGHT_BG,
            fg=FONT_COLOR,
            font=MODERN_FONT,
            command=self._toggle_menu,
        )
        # Calculate an appropriate width for each dropdown item based on the
        # longest hero name so the menu is only as wide as needed.
        font_obj = tk.font.Font(font=MODERN_FONT)
        text_width = max((font_obj.measure(h) for h in values), default=0)
        # Leave room for the icon (about 40px) and a small padding buffer.
        self.item_width = text_width + 50
        # Don't force the button to expand to the full frame width so the menu
        # remains form fitting to the hero name.
        self.button.pack()

        self.dropdown = None
        self.outside_click = None

    def _toggle_menu(self):
        if self.dropdown and self.dropdown.winfo_exists():
            self._close_menu()
            return

        self.dropdown = tk.Toplevel(self)
        self.dropdown.wm_overrideredirect(True)

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self.dropdown.geometry(f"+{x}+{y}")

        canvas = tk.Canvas(self.dropdown, bg=LIGHT_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.dropdown, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set, height=150)

        scroll_frame = tk.Frame(canvas, bg=LIGHT_BG)
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scroll_frame.bind("<Configure>", on_configure)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for hero in self.values:
            icon_path = os.path.join(ICON_DIR, f"Icon-{hero}.png")
            img = None
            if os.path.exists(icon_path):
                try:
                    original = tk.PhotoImage(file=icon_path)
                    # Scale down the 256x256 hero icons so they fit comfortably
                    # in the dropdown menu without being cropped.
                    img = original.subsample(8, 8)
                except Exception as e:
                    print(f"⚠️ Error loading image for {hero}: {e}")

            # Give each item a bit more breathing room so the icons and
            # hero names aren't crowded together.
            item_canvas = tk.Canvas(
                scroll_frame,
                width=self.item_width,
                height=40,
                highlightthickness=0,
                bg=LIGHT_BG,
            )
            rect = item_canvas.create_rectangle(
                0, 0, 0, 40, fill="#54b3d6", width=0
            )
            if img:
                # Center the icon vertically within the 40px tall item.
                item_canvas.create_image(20, 20, image=img)
                text_x = 40
            else:
                text_x = 10
            label = item_canvas.create_text(
                text_x,
                20,
                anchor="w",
                text=hero,
                fill=FONT_COLOR,
                font=MODERN_FONT,
            )
            item_canvas.image = img
            # Slight padding between items keeps the list from feeling cramped.
            item_canvas.pack(pady=1)

            anim_flag = {"running": False}
            def on_enter(e, c=item_canvas, r=rect, f=anim_flag):
                animate_highlight(c, r, 0, self.item_width, anim_flag=f)
            def on_leave(e, c=item_canvas, r=rect, f=anim_flag):
                animate_highlight(c, r, self.item_width, 0, anim_flag=f)
            def on_click(e, h=hero):
                self._select(h)

            item_canvas.bind("<Enter>", on_enter)
            item_canvas.bind("<Leave>", on_leave)
            item_canvas.bind("<Button-1>", on_click)
            item_canvas.tag_bind(label, "<Enter>", on_enter)
            item_canvas.tag_bind(label, "<Leave>", on_leave)
            item_canvas.tag_bind(label, "<Button-1>", on_click)

        root = self.button.winfo_toplevel()

        def outside(event):
            if self.dropdown and not str(event.widget).startswith(str(self.dropdown)):
                self._close_menu()

        self.outside_click = root.bind("<Button-1>", outside, add="+")

    def _select(self, value):
        self.variable.set(value)
        self._close_menu()

    def destroy(self):
        self._select(self.variable.get())
        super().destroy()

    def _close_menu(self):
        if self.dropdown and self.dropdown.winfo_exists():
            root = self.button.winfo_toplevel()
            if self.outside_click:
                root.unbind("<Button-1>", self.outside_click)
                self.outside_click = None
            self.dropdown.destroy()
            self.dropdown = None

import unicodedata
import re

def sanitize_filename(name):
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode()
    name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
    return f"Icon-{name}.png"

def create_fixed_dropdowns(frame, role_dict, layout):
    """Create dropdowns for hero selection with a scrollable list."""
    dropdowns = []  # list of (StringVar, ScrollableIconMenu, role)

    for idx, role in enumerate(layout):
        rframe = tk.Frame(frame, bg=DARK_BG)
        rframe.pack(side=tk.LEFT, padx=2)

        tk.Label(rframe, text=role, bg=DARK_BG, fg=FONT_COLOR).pack()

        hero_var = tk.StringVar(value="")

        heroes = role_dict[role]
        combo = ScrollableIconMenu(rframe, heroes, hero_var)
        combo.pack(pady=2)

        # Always show an icon label for each dropdown so every role column
        # aligns consistently.  Previously the final Support dropdown omitted
        # the icon which caused that column to appear misaligned.
        show_icon = True
        icon_label = None
        if show_icon:
            icon_label = tk.Label(rframe, bg=DARK_BG)
            icon_label.pack()

        def update_icon(*_):
            if not show_icon:
                return
            hero = hero_var.get()
            icon_path = os.path.join(ICON_DIR, f"Icon-{hero}.png")
            if os.path.exists(icon_path):
                try:
                    original = tk.PhotoImage(file=icon_path)
                    icon = original.subsample(4, 4)
                    icon_label.config(image=icon)
                    icon_label.image = icon
                except Exception as e:
                    print(f"⚠️ Error loading image for {hero}: {e}")
                    icon_label.config(image="")
                    icon_label.image = None
            else:
                icon_label.config(image="")
                icon_label.image = None

        hero_var.trace_add("write", update_icon)
        dropdowns.append((hero_var, combo, role))

    return dropdowns

def submit_match(teammates, enemies, map_var, teammate_tree, enemy_tree):
    global total_matches, match_log
    t = [d[0].get().strip() for d in teammates]
    e = [d[0].get().strip() for d in enemies]
    m = map_var.get()
    if len(set(t)) != 5 or len(set(e)) != 5 or "" in t + e or not m:
        messagebox.showerror("Error", "5 unique teammates, 5 enemies, and a map are required.")
        return
    for h in map(str.lower, t):
        teammate_matches[h] = teammate_matches.get(h, 0) + 1
        map_stats.setdefault(m, {}).setdefault("teammates", {})
        map_stats[m]["teammates"][h] = map_stats[m]["teammates"].get(h, 0) + 1
    for h in map(str.lower, e):
        enemy_matches[h] = enemy_matches.get(h, 0) + 1
        map_stats.setdefault(m, {}).setdefault("enemies", {})
        map_stats[m]["enemies"][h] = map_stats[m]["enemies"].get(h, 0) + 1
    total_matches += 1
    match_log.append({
        "teammates": t,
        "enemies": e,
        "map": m,
        "timestamp": datetime.now().isoformat()
    })
    with open(MATCH_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(match_log, f)
    save_data()
    display_stats(teammate_tree, enemy_tree)

    # clear selections to avoid accidental resubmission
    for var, _, _ in teammates + enemies:
        var.set("")
    map_var.set("")

    return None

def reset_stats(teammate_tree, enemy_tree):
    global teammate_matches, enemy_matches, total_matches, map_stats
    if messagebox.askyesno("Confirm", "Reset all stats?"):
        teammate_matches, enemy_matches, total_matches, map_stats = {}, {}, 0, {}
        save_data()
        display_stats(teammate_tree, enemy_tree)
    return None

def build_match_entry(parent):
    frame = tk.Frame(parent, bg=DARK_BG)
    tk.Label(frame, text="Select Map", bg=DARK_BG, fg=FONT_COLOR, font=MODERN_FONT).pack()
    map_var = tk.StringVar()
    map_menu = ttk.Combobox(frame, values=MAPS, textvariable=map_var, width=30)
    map_menu.pack(pady=5)

    teammate_frame = tk.Frame(frame, bg=DARK_BG); teammate_frame.pack()
    enemy_frame = tk.Frame(frame, bg=DARK_BG); enemy_frame.pack()
    tk.Label(frame, text="Teammates", bg=DARK_BG, fg=FONT_COLOR).pack()
    teammates = create_fixed_dropdowns(teammate_frame, HEROES_BY_ROLE, ["Tank", "Damage", "Damage", "Support", "Support"])
    tk.Label(frame, text="Enemies", bg=DARK_BG, fg=FONT_COLOR).pack()
    enemies = create_fixed_dropdowns(enemy_frame, HEROES_BY_ROLE, ["Tank", "Damage", "Damage", "Support", "Support"])

    bframe = tk.Frame(frame, bg=DARK_BG); bframe.pack(pady=10)

    def make_btn(text, cmd, col="#253745"):
        anim_flag = {"running": False}
        container = tk.Frame(bframe, bg=DARK_BG)
        container.pack(side=tk.LEFT, padx=5)
        canvas = tk.Canvas(container, width=160, height=30, highlightthickness=0, bg=DARK_BG)
        canvas.pack()
        rect = canvas.create_rectangle(0, 0, 0, 30, fill="#54b3d6", width=0)
        label = canvas.create_text(80, 15, text=text, fill="white", font=MODERN_FONT)

        def on_enter(e):
            canvas.itemconfig(label, fill="white")
            animate_highlight(canvas, rect, 0, 160, anim_flag=anim_flag)

        def on_leave(e):
            animate_highlight(canvas, rect, 160, 0, anim_flag=anim_flag)
            canvas.itemconfig(label, fill="white")

        def on_click(e):
            cmd()

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)
        canvas.tag_bind(label, "<Enter>", on_enter)
        canvas.tag_bind(label, "<Leave>", on_leave)
        canvas.tag_bind(label, "<Button-1>", on_click)

        return container

    history_index = [-1]
    def fill_from_log(offset=1):
        if not match_log:
            messagebox.showinfo("History", "No match history found.")
            return
        history_index[0] = (history_index[0] - offset) % len(match_log)
        entry = match_log[history_index[0]]
        map_var.set(entry["map"])
        for i, hero in enumerate(entry["teammates"]):
            teammates[i][0].set(hero)
        for i, hero in enumerate(entry["enemies"]):
            enemies[i][0].set(hero)

    make_btn("Submit", lambda: submit_match(teammates, enemies, map_var, teammate_tree, enemy_tree), MID_BG)
    make_btn("Reset Stats", lambda: reset_stats(teammate_tree, enemy_tree))
    make_btn("Same as Last Match", lambda: fill_from_log(1))

    def add_new_hero():
        name = simpledialog.askstring("Hero Name", "Enter new hero name:")
        role = simpledialog.askstring("Role", "Enter role (Tank, Damage, Support):")
        if name and role in HEROES_BY_ROLE:
            HEROES_BY_ROLE[role].append(name)
            with open(HEROES_FILE, "w") as f:
                json.dump(HEROES_BY_ROLE, f)
            # update combobox values for the affected role
            for var, combo, r in teammates + enemies:
                if r == role:
                    combo["values"] = HEROES_BY_ROLE[role]

    def add_new_map():
        new_map = simpledialog.askstring("Map Name", "Enter new map name:")
        if new_map and new_map not in MAPS:
            MAPS.append(new_map)
            map_menu["values"] = MAPS

    make_btn("Add Hero", add_new_hero)
    make_btn("Add Map", add_new_map)

    tk.Label(frame, text="Teammate Stats", bg=DARK_BG, fg=FONT_COLOR).pack()
    teammate_tree = ttk.Treeview(frame, columns=("Hero", "Pick Rate", "Games"), show="headings", height=6)
    for col in teammate_tree["columns"]: teammate_tree.heading(col, text=col)
    teammate_tree.pack(pady=5)

    tk.Label(frame, text="Enemy Stats", bg=DARK_BG, fg=FONT_COLOR).pack()
    enemy_tree = ttk.Treeview(frame, columns=("Hero", "Pick Rate", "Games"), show="headings", height=6)
    for col in enemy_tree["columns"]: enemy_tree.heading(col, text=col)
    enemy_tree.pack(pady=5)

    display_stats(teammate_tree, enemy_tree)
    return frame
def build_map_stats_page(parent):
    frame = tk.Frame(parent, bg=DARK_BG)
    map_var = tk.StringVar()
    tk.Label(frame, text="Select Map", bg=DARK_BG, fg=FONT_COLOR, font=MODERN_FONT).pack()
    map_menu = ttk.Combobox(frame, values=MAPS, textvariable=map_var, width=30)
    map_menu.pack(pady=5)

    tk.Label(frame, text="Teammate Picks", bg=DARK_BG, fg=FONT_COLOR).pack()
    teammate_tree = ttk.Treeview(frame, columns=("Hero", "Pick Count"), show="headings", height=8)
    for col in teammate_tree["columns"]: teammate_tree.heading(col, text=col)
    teammate_tree.pack(pady=5)

    tk.Label(frame, text="Enemy Picks", bg=DARK_BG, fg=FONT_COLOR).pack()
    enemy_tree = ttk.Treeview(frame, columns=("Hero", "Pick Count"), show="headings", height=8)
    for col in enemy_tree["columns"]: enemy_tree.heading(col, text=col)
    enemy_tree.pack(pady=5)

    win_rate_label = tk.Label(frame, text="", bg=DARK_BG, fg=FONT_COLOR, font=MODERN_FONT)
    win_rate_label.pack(pady=10)

    def update_map_stats(*_):
        selected = map_var.get()
        teammate_tree.delete(*teammate_tree.get_children())
        enemy_tree.delete(*enemy_tree.get_children())
        if selected in map_stats:
            wins = map_stats[selected].get("wins", 0)
            total = map_stats[selected].get("total", 0)
            rate = (wins / total * 100) if total > 0 else 0
            win_rate_label.config(text=f"Win Rate: {rate:.2f}% ({wins}/{total})")
            tstats = map_stats[selected].get("teammates", {})
            estats = map_stats[selected].get("enemies", {})
            for h, c in sorted(tstats.items(), key=lambda x: -x[1]):
                teammate_tree.insert("", "end", values=(h.title(), c))
            for h, c in sorted(estats.items(), key=lambda x: -x[1]):
                enemy_tree.insert("", "end", values=(h.title(), c))
        else:
            win_rate_label.config(text="No matches recorded.")

    map_var.trace_add("write", update_map_stats)
    return frame

def build_trend_stats_page(parent):
    frame = tk.Frame(parent, bg=DARK_BG)
    hero_var = tk.StringVar()
    tk.Label(frame, text="Select Hero to View Trends", bg=DARK_BG, fg=FONT_COLOR, font=MODERN_FONT).pack()
    hero_list = sorted(set(h for role in HEROES_BY_ROLE.values() for h in role))
    hero_menu = ttk.Combobox(frame, values=hero_list, textvariable=hero_var, width=30)
    hero_menu.pack(pady=5)

    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor("#253745")
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(pady=10)

    def update_trend_graph(*_):
        hero = hero_var.get()
        if not hero:
            return
        timestamps, pick_counts = [], []
        for entry in match_log:
            if hero in entry.get("teammates", []) + entry.get("enemies", []):
                timestamps.append(entry["timestamp"])
                pick_counts.append(pick_counts[-1] + 1 if pick_counts else 1)
        ax.clear()
        if timestamps:
            ax.plot(timestamps, pick_counts, marker="o", color="skyblue")
            ax.set_title(f"Trend of {hero} Picks Over Time", color="white")
            ax.set_xlabel("Timestamp")
            ax.set_ylabel("Cumulative Picks")
            ax.tick_params(colors='white')
        else:
            ax.set_title("No data available", color="white")
        fig.tight_layout()
        canvas.draw()

    hero_var.trace_add("write", update_trend_graph)
    return frame

root = tk.Tk()
root.title("OW2 Tracker")
root.geometry("1000x700")
root.configure(bg=DARK_BG)

sidebar = tk.Frame(root, bg=MID_BG, width=160)
sidebar.pack(side=tk.LEFT, fill=tk.Y)
main_frame = tk.Frame(root, bg=DARK_BG)
main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

pages = {}

def show_page(name):
    for f in pages.values():
        if f is not None:
            f.pack_forget()
    if pages.get(name):
        pages[name].pack(fill=tk.BOTH, expand=True)

def add_sidebar_button(name):
    btn = tk.Button(sidebar, text=name, font=MODERN_FONT, bg=LIGHT_BG, fg=FONT_COLOR, width=18, relief="flat", activebackground="#314d5f")

    def on_enter(e):
        btn.config(bg="#314d5f")

    def on_leave(e):
        btn.config(bg=LIGHT_BG)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    btn.config(command=lambda: show_page(name))
    btn.pack(pady=5)

add_sidebar_button("Match Entry")
add_sidebar_button("Map Stats")
add_sidebar_button("Trend Stats")

try:
    pages["Match Entry"] = build_match_entry(main_frame)
    print("Match Entry built")
except Exception as e:
    import traceback
    traceback.print_exc()
    pages["Match Entry"] = None
try:
    pages["Map Stats"] = build_map_stats_page(main_frame)
    print("Map Stats built")
except Exception as e:
    print("Map Stats failed:", e)
    pages["Map Stats"] = None
try:
    pages["Trend Stats"] = build_trend_stats_page(main_frame)
    print("Trend Stats built")
except Exception as e:
    print("Trend Stats failed:", e)
    pages["Trend Stats"] = None

show_page("Match Entry")
root.mainloop()