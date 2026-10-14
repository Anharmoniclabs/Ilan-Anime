# Current asset shortcuts

[Home](../../README.md) · [Repository map](../../docs/REPOSITORY_MAP.md) · [Current status](../../docs/STATUS.md)

This shelf provides readable shortcuts to the Amaia asset library and an earlier opening scene. It is separate from the [full-episode review browser](../runs/episode1-full-picture/tasks/episode-wiring/index.html) and its explicit selected motion clips. A shortcut is not an approval record; the Amaia library/puppet remains preproduction rather than a completed S01-03 shot.

## What opens where

| Shortcut | What it is | Original source |
|---|---|---|
| `Amaia - Artwork.png` | Selected Amaia master image | [amaia-assets-r2/amaia-master.png](../runs/cemi-90s-production/tasks/amaia-assets-r2/amaia-master.png) |
| `Amaia - Assets/` | Model views, expressions, mouth shapes, hands, seated poses, mother/son close-up, individual cels, prompts and EffectCraft library | [amaia-complete](../runs/cemi-90s-production/tasks/amaia-complete/) |
| `Amaia - Layered artwork.pcraft` | Editable PhotoCraft layered painting | [native/amaia-layered.pcraft](../runs/cemi-90s-production/tasks/amaia-complete/native/amaia-layered.pcraft) |
| `Amaia - Puppet.ecproj` | Editable EffectCraft puppet | [native/amaia-puppet.ecproj](../runs/cemi-90s-production/tasks/amaia-complete/native/amaia-puppet.ecproj) |
| `Amaia - Controls preview.mp4` | Puppet-control demonstration | [native/amaia-control-demo.mp4](../runs/cemi-90s-production/tasks/amaia-complete/native/amaia-control-demo.mp4) |
| `Amaia - Expression test.mp4` | Earlier expression-control test | [amaia-assets-r2/amaia-control-demo.mp4](../runs/cemi-90s-production/tasks/amaia-assets-r2/amaia-control-demo.mp4) |
| `Opening - Layered scene.pcraft` | Editable PhotoCraft scene | [s01-01/S01-01-layered.pcraft](../runs/cemi-90s-production/tasks/s01-01/S01-01-layered.pcraft) |
| `Opening - Shot.ecproj` | Editable EffectCraft scene | [s01-01/S01-01.ecproj](../runs/cemi-90s-production/tasks/s01-01/S01-01.ecproj) |
| `Opening - Edit.filmcraft` | Editable FilmCraft shot sequence | [s01-01/S01-01.filmcraft](../runs/cemi-90s-production/tasks/s01-01/S01-01.filmcraft) |
| `Opening - Preview.mp4` | Earlier opening-scene review export | [s01-01/S01-01-preview.mp4](../runs/cemi-90s-production/tasks/s01-01/S01-01-preview.mp4) |

The six `.pcraft` sheets in `Amaia - Assets/` have separate editable sources; PSD exports, generation provenance, individual cel banks and validation evidence remain in the original task directory. Keep those sources when copying or packaging the work.

## Moving the checkout

The existing shortcuts use absolute symlinks into `/home/alabs/Projects/Ilan-Anime`. They resolve in the checked local workspace but may break in another checkout. The relative **Original source** links above locate the real files without depending on those shortcut targets. Native projects may also embed absolute media paths; relink their source media in the application after moving them. Do not copy only a puppet or edit file and discard the drawings it references.
