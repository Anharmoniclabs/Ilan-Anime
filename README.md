> Current animation direction: **1990s vintage cel anime**. Episode production: [35-second opening draft](episode-01/build/take-02/opening-assembly.mp4), [shot review](episode-01/build/take-02/review.html), and [build instructions](episode-01/README.md). The earlier eight-second river test remains in `river-opening/vintage-90s/take-01/animation.mp4`.

# Anime Motion


## Production modes — Cloud / Local / Hybrid

**Cloud:** ChatGPT can read the verified Episode 1 source and selected stills,
produce artwork and motion using tools in this chat, and import actual video
candidates without requiring a local Codex/NESSA agent. **Local:** retain the
existing studio and Codex worker pipeline. **Hybrid:** convert a cloud candidate
into a local studio-engine frame sequence for finishing. All three modes
share shot timing and the independent asset/author approval gates.

Start the source-bound **15-shot / 2:06 S01 river sequence** with:

    python -m studio cloud mode cloud
    python -m studio cloud prepare S01
    python -m studio cloud status S01

See [Cloud Production](docs/CLOUD_PRODUCTION.md) and the
[actual S01 screenplay-grounded chat brief](production/cloud/briefs/S01-river.json).
The cloud bridge does not silently generate missing drawings or claim video is
finished until real media is imported and reviewed.


A local animation studio for directing image-to-video shots, comparing takes, inspecting every decoded frame and assembling a reviewed film.

## Camera and editing tooling

The local `camera_motion.py` tool provides keyframed pans, push-ins, pull-backs, easing, framing bounds, and cuts/dissolves over existing animation. It renders camera motion independently of the original cel cadence, supports 24/30/60 fps and exports through 4K. It generates no artwork. See [CAMERA.md](CAMERA.md) for presets, timeline controls and the Dairon camera test.

## Cel animation through this conversation

The new `cel_animation.py` path assembles drawings produced with the built-in imagegen tool here. It needs no video-generation account, GPU or local server. It does not call imagegen itself: the assistant creates and reviews artwork in the conversation, then runs the local compositor.

Provide a character/model sheet, ordered story keyframes and the action. The workflow is to establish character invariants, draw strong key poses and breakdowns, check construction and continuity, create missing in-betweens, then set an exposure sheet. Fast accents can use one timeline frame; moving drawings often use two; anticipation and settling poses can hold longer. Changes in drawing and spacing provide motion. Holding a drawing repeats it; it does not invent extra artwork.

```bash
python cel_animation.py cel-demo/dairon.json --out cel-demo/dairon-new-take
```

Each shot specifies one uniform sheet grid and a list of `[zero_based_cell, exposure_in_frames]` pairs. The compositor extracts cells, assembles a 24 fps video, and saves a looping GIF, separate drawing PNGs, a full timeline PNG sequence and an exposure manifest. Original sheets and prompt specifications are preserved. Use a fresh output directory for every revision. Multiple shots can be placed in one manifest in playback order.

`cel-demo/dairon-take-01/animation.mp4` is an older twelve-drawing motion test based on the user's Dairon model sheet. Generated poses have registration/spacing inconsistencies and the paddle clips in two cells. It demonstrates reference-based artwork plus uneven exposure timing. The earlier courier and jump sheets are generic technical studies, not the current production direction.

The built-in image generation runs through the connected tool; compositing and files are local. This is not a local copy of Sora, and it does not give a standalone script access to Codex/imagegen compute.

## Launch

Requires Python 3.10+ and FFmpeg/ffprobe. No Python packages or build step.

```bash
cd /home/alabs/Projects/AnimeMotion
python studio.py
```

Open http://127.0.0.1:8765. To render through fal, set `FAL_KEY` in your terminal environment before launch; never put a key in the HTML, project file or chat. A configured key is required only for cloud generation and collection. Each click on **Generate take · paid** submits one billable request. Pricing is determined by your fal account; the app does not quote or cap provider spend. There are no automatic paid retries.

1. Add your PNG/JPEG images. Each becomes a shot; upload the same reference again for another shot.
2. Fill in the shared character identity, world/lighting and visual direction.
3. Describe a concrete anticipation pose, body action and follow-through for each shot. Keep a shot to one readable action.
4. Generate a take and use **Check render** to collect it, or import a video from another generator. Imports may be up to 30 seconds / 90 MB.
5. Watch the clip, scrub its individual PNG frames, inspect the contact sheet, and check all four quality criteria. Multiple takes remain available in the take selector. **Download frames** exports the selected take's PNG sequence as a ZIP.
6. Move shots into sequence and export after selecting a reviewed take for every shot.

Project data lives in `workspace/`. Use `python studio.py --workspace /path/to/another/film --port 8766` for another film. Keep the server on localhost; it is not a hosted multiuser service. Stop with Ctrl+C.

## Animation and quality boundaries

The renderer requests actual video frames, with model interpolation disabled. It passes shared design descriptions and action beats to each generation. It does not rig characters, synthesize artist-controlled keyframes, or guarantee consistent anatomy, exact choreography or continuity. Source images should already share the desired character design and style. Prior-shot end poses are supplied as text context, not as multi-frame model conditioning.

Every decoded frame is extracted to `workspace/takes/<take>/frames/`; contact sheets are previews of those frames. Pixel-difference analysis flags mostly static clips, but camera movement, noise and morphing can pass that check. A person's visual review remains necessary. Frame extraction cannot turn a poor generated clip into good animation.

Export produces a silent MP4 with hard cuts, normalized dimensions and a 24 fps container. Where source cadence differs, frames are dropped/repeated, not redrawn. It keeps source takes and saves an edit manifest alongside each export. No soundtrack or dialogue synthesis is included.

Receipts are written before submission. If a request times out after submission, its status becomes `unknown`; the app blocks another submission for that shot. Reconcile it with your fal dashboard and the take receipt before a further purchase. Restarting the studio does not lose queue IDs or retry jobs.

## Model sources checked October 11, 2026

- [Wan 2.2 I2V contract](https://fal.ai/models/fal-ai/wan/v2.2-a14b/image-to-video/api)
- [fal queue API](https://fal.ai/docs/documentation/model-apis/inference/queue)
- [Sora 2 API retirement](https://developers.openai.com/api/docs/deprecations): API shutdown September 24, 2026. Sora is not presented as an available renderer; existing clips can be imported.

## Validation

```bash
python -m unittest -v test_studio.py
```

Tests cover frozen vs moving footage, frame extraction, review-gated export, queue receipt recovery and project validation. Synthetic test footage is a technical fixture, not an anime quality demonstration. Live paid rendering requires your credentials and images and has not been validated by these tests.

The development sandbox blocks listening sockets, so an interactive browser session could not be tested here. Launch `./Start.sh` from your desktop terminal to use the UI.

## River opening and layout locks

The first two shots from Final-1 are in `river-opening/`. See
`river-opening/README.md` for the preview, prompts, production limits and commands.
`locked_scene.py` adds fixed, nonoverlapping cel regions; the camera renderer now
checks optional protected subject bounds at every output frame.
