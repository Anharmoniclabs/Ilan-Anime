"""Initialize bounded ArtCraft production assignments; never grant approval."""
from pathlib import Path
from production.runtime import Ledger
from studio.paths import ROOT, write_json

BASE = "production/runs/episode1-craft-finish-20261015"
COMMON = ["AGENTS.md", "docs/STATUS.md", "docs/CRAFT_WORKBENCH.md",
          "production/runs/episode1-picture-motion/author-direction.json",
          "production/runs/episode1-full-picture/author-decisions.json",
          "projects/cemi_episode_01/data/EPISODE_SCRIPT.md",
          "production/runs/episode1-anime90s-scenes/shot-index.json"]

TASKS = [
    ("restore-inserts", "compositor", ["S03-03", "S04-02", "S05-13", "S06-03"],
     "Restore the four historically reviewed insert shots from their actual native EffectCraft sources into NEW output paths. Old MP4s are LFS pointers. Read original builder scripts and exact review evidence. Preserve all originals, actual timing 288/144/96/144 frames, separate layers and prescribed actions. Use ArtCraft to reopen/re-render native compositions; save new native sources, FilmCraft timeline, playable MP4s, sparse decoded evidence and exact hashes. Do not present recovered footage as new animation or transfer old approval. Inspect each result visually and technically. If a source is absent, report that exact source; do not insert stills. One submission for independent animation-supervisor review. No generation or paid services.",
     ["production/runs/episode1-native-inserts/tasks/room-filters-coin-blackout",
      "production/runs/episode1-insert-finish/tasks/native-inserts",
      "production/runs/episode1-insert-finish/reviews/native-inserts"]),
    ("memory-action", "key-animator", ["S01-04"],
     "Create the missing full 168-frame S01-04 memory-insert action through ArtCraft: three hard cuts, feverish children, lightning flash and shell-blue interior. Inspect current shot still and prior picture-draft-s01-04-v1 work and preserve references. Actual subtle breath/fever replacement drawings, authored flash frame and living transmitted light; no whole-still pan or fake action. This is an explicit image-demand assignment authorizing ONE built-in host imagegen call for missing necessary action drawings, with exact viewed reference attached and imagegen skill. No paid API/fallback. Reuse sound existing drawings where available, inspect and register generated cels. Produce editable EffectCraft and FilmCraft, 168-frame silent preview at 24fps, exposures, exact prompt, continuity evidence and result.json. Current full-episode author-direction explicitly uses 16:9; preserve existing 4:3 baseline separately. New current cast references govern. No final author approval. Stop with specific evidence if one image cannot provide coherent cels; do not mislabel failed anatomy as finished animation.",
     ["production/runs/picture-draft-s01-04-v1"]),
    ("bell-action", "key-animator", ["S01-05"],
     "Create missing 168-frame S01-05 actual action in ArtCraft: stopped soldier torches on bank, one soldier lifts bell pole and rings it hard, cut to swinging brass bell closeup. Clapper moves independently and meets rim at impacts; a flattened full-scene rotation is not action. Inspect selected new reference and all usable bell assets. This explicit image-demand assignment permits ONE built-in host imagegen call for missing action drawings using the viewed exact reference; use imagegen skill, no paid API/fallback. Reuse suitable editable art; isolate stable rigid bell/clapper/pole and registered character lift cels, preserving geometry and hands. Produce editable EffectCraft/FilmCraft, exact exposures and keyframes, 168-frame silent preview at 24fps, sparse sequence evidence and prompt. Current full-episode author-direction uses16:9; preserve 4:3 baseline separately. If one generation lacks required poses, report exact blocker instead of false completion. No final creative approval.", []),
    ("graphic-motion", "compositor", ["S03-07", "S03-11", "S08-02", "S09-04"],
     "Latest user priority: finish all116missing motion shots FIRST, no episode wiring yet. Animate these four missing graphic/editorial shots with native ArtCraft paths/text/layers at their EXACT source frame counts. S03-07 handwritten unexplained-things list scroll with47circled THE COIN; S03-11 pressed eight-second band, twelve discrete DEL presses/returns; S08-02 iris blades align to shared cemi motif for exactly3frames then unalign plus exact Aperture Civic text; S09-04 rent arithmetic orbiting/crossing out under nine-day pressure. Read exact scripts and source images and existing shared motif assets. Do not invent exact historical facts or story numbers if absent; use provided source-spec details. These are native graphic actions, no character acting or generated portraits needed unless script requires them; if actual missing required character action cannot be authored, flag incomplete. Use EffectCraft custom native paths/text/keys, separate editable elements and FilmCraft per-shot timelines; each shot needs real scripted motion, source dimensions1280x720/24fps, sparse sequential inspection and probes. Do not flatten all artwork into a pan or turn a storyboard into footage. Preserve source still and old takes. No image generation, paid calls, final approval, episode assembly or timeline wiring. Save all four previews and exact native evidence in task output. Submit separate per-shot status in shot-index.json, plus result.json for independent animation-supervisor review.", []),
    ("boy-dialogue", "key-animator", ["S01-10"],
     "User priority all116missing motion shots FIRST then wiring. Produce144-frame silent S01-10 actual boy acting draft through ArtCraft: nine-year-old boy head tilted toward offscreen bell, says exact scripted line. Read selected new source art and references; preserve current identity/costume/lighting and stable head shape. Actual replacement facial/mouth drawings and restrained eye acting, no full-image pan or morph. Explicit image-demand assignment permits ONE built-in imagegen call for distinct registered facial/mouth states attached to exact viewed current reference, using imagegen skill; focus only needed face edits, not whole multi-body pose atlas. Inspect the generated edits, retain clean reference background/shoulders, isolate coherent drawn facial cels without seams. Mouth timing is a provisional silent dialogue exposure sheet based on script, not audio-synced final lip sync; label that limitation. Save editable EffectCraft/FilmCraft,144frames24fps1280x720 where source permits; exact reference aspect preserved, no indiscriminate cropping. Save prompts, cels, exposure keys, sparse decoded evidence and SHA256s. No paid API, no approval or episode wiring. One submission to independent review; if identity/contact/drawing fails report exact issue without false complete claim.", [])]


def main():
    TASKS.append(("phone-flood", "compositor", ["S13-03"],
        "Create240-frame S13-03 phone UI text flood through editable native ArtCraft shapes/text. Exact Sofía and Denise script messages, staged fast typing on3s, exclamation cels and withheld payment overlay. Current library still is context only; this is explicitly a UI insert, not generated character acting. Preserve current palette/source context, exact spelling and all messages, no made-up amounts. Save standalone native EffectCraft/FilmCraft and silent preview with timing and hashes. No episode wiring, no paid generation or final approval. Independent review required.", []))
    TASKS.append(("memory-repair", "key-animator", ["S01-04"],
        "Repair only S01-04 exact review defects: eliminate double jaw/eyebrow remnants at12/20 with registered stable source features and clean replacement masks; replace glossy pearl/orb with current90s cel-painted shell-blue color insert, no invented pearl. Preserve correct168frames/24fps boundaries and flash56. Read previous native-v2/build.py and exact review with decoded evidence. Use one targeted built-in imagegen edit if needed for shell drawing (single asset, exact viewed references); explicit image-demand, one call, no paid fallback. No need to invent cloth lifting absent script. Existing generated facial states may be reusable with localized mouth/eyelid masks confined inside invariant face contour; inspect every pose transition. Save NEW native source and render at1280x720 if feasible, no overwriting previous attempts. Real fever facial movement must remain; cannot solve ghosting by freezing all faces. Use ArtCraft as existing build does; no episode wiring. Exact prompts/cels/native EffectCraft/FilmCraft/MP4/probes/decoded evidence and result.json for separate reviewer. User priority116missing motion first.",
        ["production/runs/episode1-craft-memory-action-20261015/tasks/memory-action",
         "production/runs/episode1-craft-memory-action-20261015/reviews/memory-action"]))
    for task_id, role, shots, objective, extra in TASKS:
        run = f"episode1-craft-{task_id}-20261015"
        ledger = Ledger(ROOT, run)
        ledger.initialize()
        if task_id in ledger.data["tasks"]:
            continue
        task = {"id": task_id, "role": role, "shots": shots, "objective": objective,
                "inputs": COMMON + extra, "output_dir": f"production/runs/{run}/tasks/{task_id}",
                "depends_on": [], "requires_author_approval": False,
                "require_host_bindings": True, "art_direction_mode": "STORY_FRAME"}
        ledger.add(task)
        ledger.dispatch(task_id, f"host-{task_id}")
        write_json(ROOT / task["output_dir"] / "envelope.json", task)
        print(run, task_id, task["output_dir"])


if __name__ == "__main__":
    main()
