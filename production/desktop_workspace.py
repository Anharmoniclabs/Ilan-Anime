"""Native desktop workspace for browsing and running local AnimeStudio scenes."""
from __future__ import annotations

import argparse
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = ImageTk = None

from studio.paths import PROJECT
from production import workspace as engine


class DesktopWorkspace:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AnimeStudio | Scene Workspace")
        self.root.geometry("1280x790")
        self.root.minsize(960, 620)
        self.colors = {
            "ink": "#1c2926", "ink_soft": "#263833", "paper": "#f1f0e8",
            "panel": "#fbfaf5", "line": "#d5d9d0", "muted": "#707c75",
            "teal": "#286d60", "gold": "#c49343", "coral": "#b95745",
            "white": "#ffffff", "red": "#a84439",
        }
        self.root.configure(background=self.colors["paper"])
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        self._configure_styles()
        self.data: dict = {}
        self.scene_map: list[dict] = []
        self.selected_scene: str | None = None
        self.preview_source: Path | None = None
        self.preview_image: ImageTk.PhotoImage | None = None
        self._build()
        self.refresh()
        self.root.after(2500, self._poll)

    def _configure_styles(self) -> None:
        c = self.colors
        self.style.configure("TFrame", background=c["paper"])
        self.style.configure("Panel.TFrame", background=c["panel"])
        self.style.configure("TLabel", background=c["paper"], foreground=c["ink"], font=("Avenir Next", 10))
        self.style.configure("Panel.TLabel", background=c["panel"], foreground=c["ink"], font=("Avenir Next", 10))
        self.style.configure("Muted.TLabel", background=c["panel"], foreground=c["muted"], font=("Avenir Next", 9))
        self.style.configure("Kicker.TLabel", background=c["paper"], foreground=c["teal"], font=("Monospace", 9, "bold"))
        self.style.configure("PanelKicker.TLabel", background=c["panel"], foreground=c["teal"], font=("Monospace", 9, "bold"))
        self.style.configure("Title.TLabel", background=c["paper"], foreground=c["ink"], font=("Georgia", 24))
        self.style.configure("Section.TLabel", background=c["panel"], foreground=c["ink"], font=("Georgia", 15))
        self.style.configure("TButton", padding=(10, 7), font=("Avenir Next", 9))
        self.style.configure("Primary.TButton", background=c["teal"], foreground=c["white"], padding=(11, 8), font=("Avenir Next", 9, "bold"))
        self.style.map("Primary.TButton", background=[("active", "#1b5148"), ("disabled", "#9ca9a3")])
        self.style.configure("Run.TButton", background=c["coral"], foreground=c["white"], padding=(11, 8), font=("Avenir Next", 9, "bold"))
        self.style.map("Run.TButton", background=[("active", "#994536"), ("disabled", "#c5a8a2")])
        self.style.configure("TEntry", fieldbackground=c["white"], padding=6)
        self.style.configure("TCombobox", fieldbackground=c["white"], padding=5)
        self.style.configure("TSeparator", background=c["line"])

    def _build(self) -> None:
        c = self.colors
        top = tk.Frame(self.root, bg=c["ink"], height=56)
        top.pack(fill="x")
        top.pack_propagate(False)
        logo = tk.Label(top, text="A", bg="#e2ba72", fg=c["ink"], font=("Georgia", 16, "bold"), width=2)
        logo.pack(side="left", padx=(17, 9), pady=13)
        tk.Label(top, text="ANIME / STUDIO", bg=c["ink"], fg="#f5f2e8", font=("Monospace", 10, "bold")).pack(side="left")
        tk.Label(top, text="HERALDS OF THE CEMÍ   /   EPISODE 01", bg=c["ink"], fg="#c5cec7", font=("Monospace", 9)).pack(side="left", padx=28)
        self.policy_label = tk.Label(top, text="Checking generation policy", bg=c["ink"], fg="#e1c58e", font=("Monospace", 9))
        self.policy_label.pack(side="right", padx=17)

        body = ttk.Frame(self.root)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        self._build_sidebar(body)
        self._build_workarea(body)
        self.status = tk.StringVar(value="Local project files · no browser server")
        footer = tk.Label(self.root, textvariable=self.status, anchor="w", padx=12, pady=5,
                          bg="#e8e8df", fg=c["muted"], font=("Monospace", 8))
        footer.pack(fill="x", side="bottom")

    def _build_sidebar(self, parent: ttk.Frame) -> None:
        c = self.colors
        side = tk.Frame(parent, bg="#e8e8df", width=248, highlightthickness=0)
        side.grid(row=0, column=0, sticky="ns")
        side.grid_propagate(False)
        tk.Label(side, text="EPISODE TIMELINE", bg="#e8e8df", fg=c["teal"], font=("Monospace", 9, "bold")).pack(anchor="w", padx=15, pady=(19, 2))
        head = tk.Frame(side, bg="#e8e8df")
        head.pack(fill="x", padx=15, pady=(0, 10))
        tk.Label(head, text="Scenes", bg="#e8e8df", fg=c["ink"], font=("Georgia", 21)).pack(side="left")
        self.scene_total = tk.Label(head, text="—", bg="#e8e8df", fg=c["muted"], font=("Monospace", 9))
        self.scene_total.pack(side="left", padx=8, pady=(5, 0))
        self.search = tk.StringVar()
        search = ttk.Entry(side, textvariable=self.search)
        search.pack(fill="x", padx=12, pady=(0, 8))
        search.insert(0, "Search scenes")
        search.bind("<FocusIn>", lambda _event: search.delete(0, "end") if search.get() == "Search scenes" else None)
        search.bind("<KeyRelease>", lambda _event: self._paint_scene_list())
        list_frame = tk.Frame(side, bg="#e8e8df")
        list_frame.pack(fill="both", expand=True, padx=8)
        self.scene_list = tk.Listbox(list_frame, activestyle="none", exportselection=False,
                                     bg="#e8e8df", fg=c["ink"], selectbackground=c["panel"],
                                     selectforeground=c["ink"], highlightthickness=0, borderwidth=0,
                                     font=("Monospace", 9), relief="flat")
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.scene_list.yview)
        self.scene_list.configure(yscrollcommand=scroll.set)
        self.scene_list.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.scene_list.bind("<<ListboxSelect>>", self._scene_selected)
        tk.Frame(side, height=1, bg=c["line"]).pack(fill="x", side="bottom")
        tk.Label(side, text="24 FPS  ·  EPISODE SPECS", bg="#e8e8df", fg=c["muted"],
                 font=("Monospace", 8), pady=10).pack(side="bottom", anchor="w", padx=14)

    def _build_workarea(self, parent: ttk.Frame) -> None:
        c = self.colors
        area = ttk.Frame(parent, padding=(21, 15, 20, 12))
        area.grid(row=0, column=1, sticky="nsew")
        area.columnconfigure(0, weight=1)
        area.rowconfigure(1, weight=1)
        head = ttk.Frame(area)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        head.columnconfigure(0, weight=1)
        ttk.Label(head, text="SHOT WORKSPACE  /  LOCAL FILES", style="Kicker.TLabel").grid(row=0, column=0, sticky="w")
        self.shot_title = ttk.Label(head, text="Choose a scene", style="Title.TLabel")
        self.shot_title.grid(row=1, column=0, sticky="w", pady=(1, 0))
        self.render_button = ttk.Button(head, text="▶  Render draft", style="Primary.TButton", command=self._render, state="disabled")
        self.render_button.grid(row=0, column=1, rowspan=2, sticky="e", padx=(8, 0))

        left = ttk.Frame(area)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        self.preview_meta = ttk.Label(left, text="SCENE PREVIEW  ·  SELECT A SHOT", style="Kicker.TLabel")
        self.preview_meta.grid(row=0, column=0, sticky="w", pady=(3, 6))
        self.preview = tk.Label(left, text="Select a scene to inspect its local keyframe or render.",
                                bg="#202b29", fg="#e7e7dc", font=("Georgia", 14),
                                compound="center", justify="center")
        self.preview.grid(row=1, column=0, sticky="nsew")
        self.preview.bind("<Configure>", self._resize_preview)
        buttons = ttk.Frame(left)
        buttons.grid(row=2, column=0, sticky="ew", pady=(7, 0))
        self.open_art = ttk.Button(buttons, text="Open reference file", command=self._open_reference, state="disabled")
        self.open_art.pack(side="left")
        self.open_spec = ttk.Button(buttons, text="Open scene spec", command=self._open_spec, state="disabled")
        self.open_spec.pack(side="left", padx=(6, 0))
        self.open_render_button = ttk.Button(buttons, text="Open latest render", command=self._open_render, state="disabled")
        self.open_render_button.pack(side="right")
        ttk.Label(left, text="ACTION", style="Kicker.TLabel").grid(row=3, column=0, sticky="w", pady=(13, 3))
        self.action_text = tk.Label(left, text="Shot action will appear here.", bg=c["paper"], fg=c["ink"],
                                    justify="left", anchor="nw", wraplength=650, font=("Georgia", 13))
        self.action_text.grid(row=4, column=0, sticky="ew")
        self.truth_text = ttk.Label(left, text="Shot specs describe build instructions, not finished animation.", style="Muted.TLabel", wraplength=650)
        self.truth_text.grid(row=5, column=0, sticky="w", pady=(10, 0))

        self._build_inspector(area)
        jobs = ttk.Frame(area)
        jobs.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(17, 0))
        jobs.columnconfigure(0, weight=1)
        heading = ttk.Frame(jobs)
        heading.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        ttk.Label(heading, text="WORKSPACE JOBS", style="Kicker.TLabel").pack(side="left")
        self.job_count = ttk.Label(heading, text="No jobs", style="Muted.TLabel")
        self.job_count.pack(side="right")
        self.jobs_list = tk.Listbox(jobs, height=4, activestyle="none", exportselection=False,
                                    bg=c["panel"], fg=c["ink"], selectbackground=c["soft_green"] if "soft_green" in c else "#dce8df",
                                    highlightthickness=1, highlightbackground=c["line"], borderwidth=0,
                                    font=("Monospace", 8))
        self.jobs_list.grid(row=1, column=0, sticky="ew")
        self.jobs_list.bind("<<ListboxSelect>>", self._job_selected)
        self.job_output = tk.Text(jobs, height=3, wrap="word", state="disabled", bg="#e8e9e1", fg=c["muted"],
                                  relief="flat", font=("Monospace", 8), padx=7, pady=5)
        self.job_output.grid(row=2, column=0, sticky="ew", pady=(4, 0))

    def _build_inspector(self, parent: ttk.Frame) -> None:
        c = self.colors
        box = tk.Frame(parent, bg=c["panel"], highlightbackground=c["line"], highlightthickness=1, width=286)
        box.grid(row=1, column=1, sticky="ns")
        box.grid_propagate(False)
        tk.Label(box, text="SCENE RECORD", bg=c["panel"], fg=c["teal"], font=("Monospace", 9, "bold")).pack(anchor="w", padx=13, pady=(13, 8))
        self.properties: dict[str, tk.StringVar] = {}
        for key, title in (("status", "Status"), ("duration", "Duration"), ("stage", "Drawing"),
                           ("animation", "Animation"), ("camera", "Camera"), ("reference", "Reference")):
            row = tk.Frame(box, bg=c["panel"])
            row.pack(fill="x", padx=13, pady=3)
            tk.Label(row, text=title, width=10, anchor="w", bg=c["panel"], fg=c["muted"], font=("Avenir Next", 8)).pack(side="left")
            value = tk.StringVar(value="—")
            self.properties[key] = value
            tk.Label(row, textvariable=value, anchor="w", justify="left", wraplength=150,
                     bg=c["panel"], fg=c["ink"], font=("Avenir Next", 8, "bold")).pack(side="left", fill="x", expand=True)

        tk.Frame(box, height=1, bg=c["line"]).pack(fill="x", pady=(11, 12))
        tk.Label(box, text="PRODUCTION RUN", bg=c["panel"], fg=c["teal"], font=("Monospace", 9, "bold")).pack(anchor="w", padx=13)
        self.run_select = ttk.Combobox(box, state="readonly")
        self.run_select.pack(fill="x", padx=12, pady=(8, 3))
        self.run_select.bind("<<ComboboxSelected>>", lambda _event: self._paint_run())
        self.run_summary = tk.Label(box, text="Loading ledgers…", bg=c["panel"], fg=c["muted"], anchor="w", font=("Monospace", 8))
        self.run_summary.pack(fill="x", padx=13, pady=(3, 6))
        task_frame = tk.Frame(box, bg=c["panel"])
        task_frame.pack(fill="both", expand=True, padx=11)
        self.task_list = tk.Listbox(task_frame, activestyle="none", exportselection=False,
                                    bg=c["panel"], fg=c["ink"], highlightthickness=1,
                                    highlightbackground=c["line"], borderwidth=0, font=("Monospace", 8))
        task_scroll = ttk.Scrollbar(task_frame, orient="vertical", command=self.task_list.yview)
        self.task_list.configure(yscrollcommand=task_scroll.set)
        self.task_list.pack(side="left", fill="both", expand=True)
        task_scroll.pack(side="right", fill="y")
        self.run_button = ttk.Button(box, text="↗  Run next task", style="Run.TButton", command=self._run_one, state="disabled")
        self.run_button.pack(fill="x", padx=12, pady=(9, 4))
        self.dry_button = ttk.Button(box, text="Preview next task", command=self._dry_run, state="disabled")
        self.dry_button.pack(fill="x", padx=12, pady=(0, 5))
        tk.Label(box, text="One task per click. Paused runs need explicit CLI recovery. Generation follows repository policy and task budget.",
                 bg=c["panel"], fg=c["muted"], justify="left", wraplength=254, font=("Avenir Next", 8)).pack(anchor="w", padx=13, pady=(2, 12))

    def refresh(self) -> None:
        try:
            previous_run = self.run_select.get() if hasattr(self, "run_select") else ""
            self.data = engine.snapshot()
            self.scene_map = self.data["scene_specs"]
            self.policy_label.config(text=(f"GENERATION ON  ·  ${self.data['generation']['spent_usd']:.2f} / ${self.data['generation']['cap_usd']:.2f}"
                                           if self.data["generation"]["enabled"] else "GENERATION OFF  ·  $0 BUDGET"))
            self._paint_scene_list()
            if self.selected_scene not in {shot["id"] for shot in self.scene_map}:
                self.selected_scene = self.scene_map[0]["id"] if self.scene_map else None
            self._paint_shot()
            self._paint_runs(previous_run)
            self._paint_jobs()
            self.status.set(f"Connected to project files at {PROJECT}  ·  {len(self.scene_map)} scene specs")
        except Exception as exc:
            self.status.set(f"Could not load project data: {exc}")

    def _paint_scene_list(self) -> None:
        if not hasattr(self, "scene_list"):
            return
        query = self.search.get().lower().strip()
        self.scene_list.delete(0, "end")
        self._visible_scenes = [shot for shot in self.scene_map if query in f"{shot['id']} {shot['action']} {shot['status']}".lower()]
        for shot in self._visible_scenes:
            status_mark = "●" if shot["preview"] else "○"
            self.scene_list.insert("end", f"{status_mark}   {shot['id']}   {shot['status'].replace('_', ' ')}")
            self.scene_list.itemconfig("end", foreground=self.colors["teal"] if shot["preview"] else self.colors["muted"])
        self.scene_total.config(text=str(len(self.scene_map)))
        if self.selected_scene:
            for index, shot in enumerate(self._visible_scenes):
                if shot["id"] == self.selected_scene:
                    self.scene_list.selection_set(index)
                    self.scene_list.see(index)
                    break

    def _scene_selected(self, _event=None) -> None:
        selection = self.scene_list.curselection()
        if not selection:
            return
        self.selected_scene = self._visible_scenes[selection[0]]["id"]
        self._paint_shot()
        self._paint_run()

    def _paint_shot(self) -> None:
        shot = next((item for item in self.scene_map if item["id"] == self.selected_scene), None)
        if not shot:
            return
        self.shot_title.config(text=shot["id"])
        self.preview_meta.config(text=f"SCENE PREVIEW  ·  {shot['fps']} FPS  ·  {shot['frames']} FRAMES")
        self.action_text.config(text=shot["action"] or "No action description is attached to this spec.")
        self.truth_text.config(text=shot["truth"] or "Shot specs describe build instructions, not finished animation.")
        reference = shot["preview"]
        self.preview_source = engine.project_file(reference) if reference else None
        self.open_art.configure(state="normal" if self.preview_source else "disabled")
        spec_path = PROJECT / "data" / "shots" / f"{shot['id']}.json"
        self.open_spec.configure(state="normal" if spec_path.is_file() else "disabled")
        render_path = engine.project_file(shot["render"]) if shot["render"] else None
        self.open_render_button.configure(state="normal" if render_path else "disabled")
        self.properties["status"].set(shot["status"].replace("_", " "))
        self.properties["duration"].set(f"{shot['frames'] / shot['fps']:.2f}s · {shot['frames']}f")
        self.properties["stage"].set(shot["stage"])
        self.properties["animation"].set(shot["animation_status"].replace("_", " "))
        self.properties["camera"].set(shot["camera"] or "Not specified")
        self.properties["reference"].set(reference.split("/")[-1] if reference else "No keyframe")
        busy = any(job["state"] in ("queued", "running") for job in self.data.get("jobs", []))
        self.render_button.configure(state="disabled" if busy else "normal")
        self._load_preview()

    def _load_preview(self) -> None:
        shot = next((item for item in self.scene_map if item["id"] == self.selected_scene), None)
        if not shot:
            return
        path = self.preview_source
        if path is None:
            self.preview.configure(image="", text="No keyframe attached to this scene.\nThe spec remains available on disk.")
            self.preview_image = None
            return
        try:
            width = max(260, self.preview.winfo_width() - 12)
            height = max(150, self.preview.winfo_height() - 12)
            if Image is not None:
                image = Image.open(path).convert("RGB")
                image.thumbnail((width, height), Image.Resampling.LANCZOS)
                self.preview_image = ImageTk.PhotoImage(image)
            else:
                image = tk.PhotoImage(file=str(path))
                factor = max(1, (image.width() + width - 1) // width, (image.height() + height - 1) // height)
                self.preview_image = image.subsample(factor, factor)
            self.preview.configure(image=self.preview_image, text="")
        except (OSError, tk.TclError) as exc:
            self.preview.configure(image="", text=f"Could not preview local image:\n{exc}")

    def _resize_preview(self, _event=None) -> None:
        if self.preview_source:
            self.root.after_idle(self._load_preview)

    def _paint_runs(self, previous: str = "") -> None:
        runs = self.data.get("runs", {}).get("runs", [])
        values = [f"{run['id']}{'  ·  PAUSED' if run['paused'] else ''}" for run in runs]
        self._run_lookup = {value: run for value, run in zip(values, runs)}
        self.run_select["values"] = values
        if previous in self._run_lookup:
            self.run_select.set(previous)
        elif values and not self.run_select.get():
            self.run_select.current(0)
        self._paint_run()

    def _selected_run(self) -> dict | None:
        return self._run_lookup.get(self.run_select.get()) if hasattr(self, "_run_lookup") else None

    def _paint_run(self) -> None:
        run = self._selected_run()
        self.task_list.delete(0, "end")
        if not run:
            self.run_summary.config(text="No production ledgers")
            self.run_button.configure(state="disabled")
            self.dry_button.configure(state="disabled")
            return
        self.run_summary.config(text=f"{run['task_count']} TASKS  ·  {run['open_task_count']} OPEN  ·  {'PAUSED' if run['paused'] else 'READY'}")
        tasks = run["tasks"]
        shot_id = self.selected_scene
        relevant = [task for task in tasks if not task.get("shots") or shot_id in task.get("shots", [])]
        for task in relevant[:100]:
            self.task_list.insert("end", f"{task['state'].upper():<13} {task['id']}")
            self.task_list.insert("end", f"    {task['role']} · {', '.join(task.get('shots') or []) or 'episode-wide'}")
            self.task_list.insert("end", f"    {task['objective'][:220]}")
            self.task_list.insert("end", "")
        if not relevant:
            self.task_list.insert("end", "No tasks for this scene in the selected ledger.")
        busy = any(job["state"] in ("queued", "running") for job in self.data.get("jobs", []))
        can_run = not run["paused"] and run["open_task_count"] > 0 and not busy
        state = "normal" if can_run else "disabled"
        self.run_button.configure(state=state)
        self.dry_button.configure(state=state)

    def _paint_jobs(self) -> None:
        self._jobs = list(reversed(self.data.get("jobs", [])))
        self.jobs_list.delete(0, "end")
        for job in self._jobs:
            self.jobs_list.insert("end", f"{job['state'].upper():<10} {job['label']}")
        self.job_count.config(text=f"{len(self._jobs)} tracked" if self._jobs else "No jobs")
        busy = any(job["state"] in ("queued", "running") for job in self._jobs)
        self.render_button.configure(state="disabled" if busy or not self.selected_scene else "normal")
        self._paint_run()

    def _job_selected(self, _event=None) -> None:
        selection = self.jobs_list.curselection()
        if not selection:
            return
        job = self._jobs[selection[0]]
        self.job_output.configure(state="normal")
        self.job_output.delete("1.0", "end")
        self.job_output.insert("1.0", job.get("output") or "Engine process is working…")
        self.job_output.configure(state="disabled")

    def _start(self, kind: str, **payload) -> None:
        try:
            job = engine.start_job(kind, payload)
            self.status.set(f"Started {job['label']}")
            self.refresh()
        except (ValueError, OSError) as exc:
            messagebox.showerror("Could not start engine job", str(exc), parent=self.root)

    def _render(self) -> None:
        shot = self.selected_scene
        if shot and messagebox.askyesno("Render local draft", f"Render {shot} as a draft using its local shot spec?", parent=self.root):
            self._start("render", shot=shot)

    def _run_one(self) -> None:
        run = self._selected_run()
        if run and messagebox.askyesno("Run one production task", f"Run at most one task in {run['id']}? The repository's generation policy still applies.", parent=self.root):
            self._start("run", run=run["id"])

    def _dry_run(self) -> None:
        run = self._selected_run()
        if run:
            self._start("run", run=run["id"], dry_run=True)

    def _open_path(self, path: Path) -> None:
        try:
            subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as exc:
            messagebox.showerror("Could not open local file", str(exc), parent=self.root)

    def _open_reference(self) -> None:
        if self.preview_source:
            self._open_path(self.preview_source)

    def _open_spec(self) -> None:
        if self.selected_scene:
            spec = PROJECT / "data" / "shots" / f"{self.selected_scene}.json"
            if spec.is_file():
                self._open_path(spec)

    def _open_render(self) -> None:
        shot = next((item for item in self.scene_map if item["id"] == self.selected_scene), None)
        if shot and shot["render"]:
            self._open_path(engine.project_file(shot["render"]))

    def _poll(self) -> None:
        self.refresh()
        self.root.after(2500, self._poll)


def main(argv: list[str] | None = None) -> None:
    argparse.ArgumentParser(description="Open the local AnimeStudio desktop workspace.").parse_args(argv)
    root = tk.Tk()
    DesktopWorkspace(root)
    root.mainloop()


if __name__ == "__main__":
    main()