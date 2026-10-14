# S01-07 independent animation review

**Decision: reject.** The seven-second file is a usable blocking/source-drawing draft, not an accepted writing-action shot. Creator `/root/counter_writing`; reviewer `/root/review_counter_writing` (binding confirmed by coordinator).

Clip SHA256: `b450b7c5fdfa20be3161d4cb6f573e2c25b5ab9e49c15730aedd1cf96cefac6c`.

## F1 — major — 1.000-2.958s; 3.875-5.958s

Each line uses only four writing poses. Holds last 9-18 frames (0.375-0.750s); the pen and new ink jump between fixed locations instead of articulating the writing strokes. The final lift is held for a full second. A clock divisible by three does not make these writing actions animate on 3s.

Required fix: Add registered hand/wrist/quill breakdowns for active strokes at 3-frame exposures; retain long holds only for intentional setup or punctuation. Show nib tracing each developing ink segment and settle at each line end.

## F2 — major — 2.958->3.000s; 3.458->3.500s; 3.833->3.875s; 5.958->6.000s

Lift and return have no intervening poses. At f71->72 the declared nib changes from (374,181) to (336,123), about 92px left and 141px up in output space in one exposure change. Hand silhouette and cuff mass pop with it; this is a pose jump rather than a readable lift arc.

Required fix: Draw contact release, rising wrist, apex, return and landing breakdowns; preserve grip geometry and follow an intentional arc with short exposures.

## F3 — major — 3.500s; 3.875s; 5.250s; 6.000s

Polygon extraction introduces visible seams and clipped anatomy/prop contours. At f93 the translated upper-left coat region has a hard horizontal rectangular seam about 20px below the image top. At f84/144 the cuff and hand edges have hard stair-step cuts; raised feather edges are flattened/clipped. f126 puts the second-line nib at the page fore-edge/gutter region rather than confidently on the paper writing surface.

Required fix: Extract only the changing arm and pen along their real ink contours with antialiased mattes, retain a clean fixed torso plate, and draw the lower-line poses against the ledger plane instead of translating the whole bank down 8px. Repair clipped quill/hand contours and verify every nib contact on paper.

## F4 — moderate — 3.000-3.833s; 6.000-6.958s

The exposed marks are two uniform sinusoidal zigzags rather than varied pen strokes. They appear in large increments when the hand changes pose, reducing legibility of the intended act of writing. No readable words are required, but stroke variation and drawing-on must track the nib.

Required fix: Use nonverbal handwriting-like marks with varied stroke lengths and gaps, registered to page perspective and revealed in contact with the nib.

## Checks that pass

- 168 frames, 24fps, 1280x720, 7 seconds; all frames independently decode
- The establishing source retains seated down gaze, brown costume, ledger and moonless mangrove
- Locked ledger and supporting hand avoid prop deformation during closeup; two lines and separate lift beats are represented
- EffectCraft references 12 retained still sources and FilmCraft references retained MP4; no missing native paths and all declared input SHA256 values match. Deleted render cache is not required by these saved native projects

## Inspection limits

Independently decoded all 168 frames; visually inspected boundary sequence and full-size detail frames, exact source and style reference. Timing conclusions use exposure durations and decoded boundaries. No real-time desktop playback or native GUI reopen was performed. Native references were checked structurally and all retained still hashes match. No sound was reviewed. Technical review cannot grant author approval.
