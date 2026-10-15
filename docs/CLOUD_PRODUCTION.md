# Ilan-Anime: ChatGPT Cloud, Local and Hybrid production

Cloud, Local and Hybrid are equal production modes sharing the **same episode
source, shot IDs, exact frame timing, selected references, art direction and
asset-registry approval gates**. A mode never changes what "finished" means.

## Cloud means direct work in the ChatGPT conversation

ChatGPT reads source material via connected GitHub/Drive, creates artwork with
the tools actually available in the chat, renders or imports real media and
submits it as a scene candidate. It does not need Codex, NESSA or a local
model or agent daemon.

This CLI is a handoff protocol, not an API for the built-in ChatGPT image
generator. Standalone Python cannot invoke chat-only image tools. If a video
renderer is unavailable, generate source art and report the motion blocker,
not an invented MP4 or static pan mislabeled as animation.

| Mode | Execution | Asset/approval authority |
|---|---|---|
| Cloud | ChatGPT tools + cloud-created image/clip files | Shared episode and registry |
| Local | Existing Codex/NESSA + desktop engines | Shared episode and registry |
| Hybrid | Cloud clip imported as local frame sequence, or local references used in chat | Shared episode and registry |

The mode setting selects a routing preference; it does not start local
processes, change security policy or spend money.

## Episode 1 opening river scene

S01 contains **15 shots / 3024 frames / 2:06**, at **24fps** with the
current **1280x720 16:9** specification. It starts at the episode body
timecode 00:09:00, after the two opening cards.

Commands:

    python -m studio cloud mode cloud
    python -m studio cloud prepare S01
    python -m studio cloud status S01

Preparation writes the scene packet and chat handoff under
production/cloud/scenes/S01/. The packet reads the current episode script
and selected-still index, carries input SHA-256 hashes, states the correct
frame count and all required actions, and labels references exploratory
until individually approved.

The committed production/cloud/briefs/S01-river.json also supplies a
read-only chat kickoff manifest: selected stills, exact shot IDs and actions.

For each actual completed *candidate* clip, import it without using a local
agent:

    python -m studio cloud ingest S01 S01-05 /path/to/real-clip.mp4 --evidence /path/to/actual-review.json

The input must be a real MP4 of the correct dimensions, frame rate and exact
decoded frame count. Its SHA-256 is recorded with source hashes. The file is
copied to an immutable submission folder and marked **submitted**, never
approved or canonical. Changed re-takes require a new revision, not an
overwrite of a prior result.

To hand off that cloud clip to the local engine:

    python -m studio cloud bridge S01 S01-05

This extracts every frame and writes an exploratory studio-engine shot spec.
The flattened video does NOT recreate separate paint layers, original
drawings or a genuine arm rig. Save native layers separately where possible.

Once ALL 15 clips are present and hash/frame-verified, an inspection-only
silent scene cut can be assembled:

    python -m studio cloud assemble-draft S01 --out /path/to/S01-review.mp4

The command refuses missing shots, changed media, wrong frame counts and
overwriting outputs. It never bypasses the final-release approval process.

## The bell-action technical acceptance test: S01-05

The previous generation attempt failed because the soldier's pole grip
moved between poses, and bell/clapper separation was missing. We will
not pretend this can be repaired by rotating a whole source image.

1. Lock the pole as one rigid prop with unchanged length and two
   independently attached hand-contact parameters. Animate a grip change
   only if an explicitly drawn regrip exists.
2. Define shoulder, elbow, wrist and hand anchors for both arms; use IK or
   authored replacement drawings that maintain upper/lower arm lengths.
3. Define the bell pivot and its rim in local geometry. Move the bell
   shell and hinged clapper independently. Specify impact frame indices
   and verify the clapper tip meets the rim at each impact.
4. Measure every one of 168 frames, not only attractive key poses.
   Run the following on real observed-position evidence:

       python -m studio cloud validate-action /path/to/S01-05-measured.json

   Sparse keys can pass their measured geometry but must report
   mechanics_verified=false and complete_frame_coverage=false.
5. Artistically animate anticipation, weight transfer, lift, shake and
   follow-through using the canonical soldier reference. A geometry
   checker does not invent credible acting, recognize perfect anatomy or
   separate missing cels automatically. Draw breakdowns and corrections.
6. Play the actual animation, frame-step all hand/pole and bell/clapper
   contacts, inspect anatomy, sound and source art identity. Record exact
   visual evidence and require independent technical review and author
   approval of that specific immutable take.

This approach solves **mechanical enforcement and truthful validation**.
It does not claim automatic photo-to-perfect-anime acting. When necessary
drawings are unavailable, flag and block the shot.

## Technical boundaries

- The cloud handoff does not import Codex or require a configured LLM runtime.
- It uses standard-library Python and calls ffprobe/ffmpeg only for video.
- No cloud provider credentials, payments, generation retries or scheduling.
- A locally approved task does not approve a changed cloud file.
- Receipts are provisional evidence, not canonical entries in the existing
  production/asset-registry.json. Final acceptance uses the same established
  registrar, independent reviewer and author gate.
- ChatGPT can generate media with tools available in the current chat. If a
  tool is unavailable, the workflow explicitly reports the missing capability.
- Test with: python -m unittest discover -s tests -p test_cloud.py -v

Runtime tests validate contracts, not cinematography or expressive acting.
