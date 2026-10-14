# Ilan-Anime Craft workbench

The coordinator can now operate all seven installed Craft engines. This is a
headless engine connection, not control of an already-open GUI window. Native
projects are saved so you can open them in the desktop apps. No new downloads,
cloud generation or paid providers are involved in these commands.

Run commands from Ilan-Anime using `.venv/bin/python -m studio craft …`.
The MCP transport is reused from the sibling Nessa checkout; set
`ILAN_NESSA_ROOT=/path/to/NESSA` if it moves. The Craft CLIs must be on PATH or in
`~/.local/bin`. Their schemas are discovered live rather than assumed.

## Production routing

| Stage | Engine and handoff |
|---|---|
| Script, boards and model-sheet book | PdfCraft inspection; DesignCraft editable layouts/PDFs |
| Sketches, cleanup, backgrounds and cel paint | PhotoCraft native documents and full-canvas PNG exports |
| Vector linework, rigid props and typography | VectorCraft SVG/PDF exports |
| Reference development | LightCraft; preserve source and approved palette |
| Registered poses and frame timing | Existing `studio layers` and `studio motion`; explicit exposure manifests |
| 3D sets, props and renders | Existing `studio blender`; feed registered PNG renders into the same handoff |
| Compositing and effects | EffectCraft native composition plus PNG sequence |
| Editing and sound placement | FilmCraft editable sequence; existing `studio sound` for dialogue/mix |
| Review and final delivery | Existing independent worker/reviewer, `studio qa`, registry and author gates |

The apps provide editing/rendering engines. They do not automatically draw missing
poses, invent good in-betweens, register anatomy, generate voices, or establish
finished anime quality. Existing image-demand workers remain responsible for
artwork. The new path preserves Ilan-Anime's 16:9, 24 fps contract.

## Discover and operate engines

```bash
python -m studio craft doctor --out production/craft-check-new
python -m studio craft tools photocraft --query layer --out production/photo-tools-new
python -m studio craft run production/examples/craft-workbench-check.json --out production/craft-check-take-new
```

The example makes technical fixtures across painting, vectors, development and
page-layout apps, then inspects the resulting PDF. It is not episode artwork.
Recipes contain ordered `{app, tool, arguments}` steps. `${ROOT}` expands to the
Ilan-Anime root; `${OUT}` expands to this invocation's output directory. One live
session per app preserves in-memory state across steps. Discover command IDs and
parameters through the app's command-list tools before authoring recipes. Save
native files explicitly; process exit discards unsaved state.

An optional `outputs` list names nonempty files required beneath `${OUT}`.
The recipe runner is a trusted local automation runner, not an OS sandbox: recipe
arguments and scripting tools can access files beyond the output directory.
Workers must obey their assigned output scope. Recipes do not expose output-value
substitution; use the Python `Session` interface when subsequent calls need IDs.

## Drawings to an editable shot

Prepare registered PNGs, all the same full canvas size. A cel may have alpha;
`background` is optional. Each exposure is an existing drawing held for exactly
the specified number of frames. Paths are relative to the manifest.

```json
{
  "shot": "S01-11",
  "width": 1280,
  "height": 720,
  "fps": 24,
  "background": "background.png",
  "exposures": [
    {"path": "hover.png", "frames": 3},
    {"path": "contact.png", "frames": 2},
    {"path": "impact.png", "frames": 1}
  ]
}
```

```bash
python -m studio craft cels path/to/exposures.json --out production/craft-shots/S01-11-take-new
```

The command snapshots and hashes inputs, saves `shot.ecproj`, renders every PNG
into `frames/`, encodes `preview.mp4`, checks its dimensions/frame rate/count,
and saves `edit.filmcraft` with the clip in a matching timeline. `studio-shot.json`
also exposes the same drawings and timing to Ilan-Anime's existing compositor:

```bash
python -m studio render production/craft-shots/S01-11-take-new/studio-shot.json --draft --out production/craft-shots/S01-11-take-new/local-review.mp4
```

This convenience compositor supports one ordered cel track and an optional static
background. For independently moving characters, backgrounds, camera and effects,
use the existing multilayer studio spec or a custom EffectCraft recipe. It does
not flatten a complex shot into this limited manifest automatically. Audio is not
generated or added by `craft cels`. Keep the output directory together: native
projects reference its input snapshots and preview. Projects use absolute paths;
moving them requires relinking.

## Receipts and recovery

Every call records arguments before execution and the engine response afterward.
A disconnected/timed-out call is `unknown`, not safe to retry. Batches stop on
engine errors, including nested error results. Interrupted output remains in
place for inspection; existing take directories are never overwritten. Use a
fresh output directory only after examining partial work. No production ledger,
asset approval or spending policy is changed by these commands.

## Validation

All seven engines connected locally. Tests exercise actual EffectCraft import,
exact drawing holds, alpha/background compositing, PNG and MP4 generation,
FilmCraft timeline creation, and reopening both saved native projects. They also
cover output preservation, invalid exposures and stopping after recipe failure.

```bash
ILAN_CRAFT_INTEGRATION=1 .venv/bin/python -m unittest discover -s tests -p test_studio_craft.py -v
```

Evidence is under `production/craft-validation/`. The initial `cels-v1` fixture
failed visual timing checks because numbered stills were auto-imported as image
sequences. `cels-v2` corrects this with non-numeric still filenames; the automated
regression now checks pixel holds and alpha. These are technical fixtures, not
approved episode shots.

`cels-v3` additionally verifies the handoff back to the existing local compositor.
`workbench-v2` completes the 13-step multi-app recipe; its first pass exposed
PhotoCraft's relative-path requirement, now normalized by the adapter.
