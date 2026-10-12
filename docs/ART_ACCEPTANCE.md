# Cemí art acceptance contract

`production/art_direction.json` turns the canonical art direction into a versioned review contract. It preserves the four distinct deliverable modes, source precedence, visual rules and promotion gates. It does **not** turn taste into a score and does not claim that software inspected image pixels.

## What “10/10” means here

A canonical asset must satisfy every required criterion for its mode with concrete evidence, pass an independent technical/art review and receive Luis M. Minier's explicit approval for the exact SHA-256 asset digest. Technical approval and author approval are separate. A report cannot average away a failed identity, style, action, text or geometry check.

The source order is:

1. Original pencil portraits for identity and artist signature.
2. Author-approved illustrated overview for finish, material, marks and editorial mood.
3. Option B Moody Urban Dusk for lighting and color.
4. Character bible and later author corrections for character continuity.

Lower-priority references cannot override higher-priority identity evidence. A generated mood board is not identity canon. Rejected work is terminal at that version: revision requires a new asset ID/digest and the complete review path.

## Production modes

| Mode | Intended output | Critical boundary |
|---|---|---|
| `CHARACTER_ASSET` | One named character or explicitly requested multi-view sheet | Complete hands/shoes, stable accessories, no collage or text |
| `ENVIRONMENT_PLATE` | Context-specific clean/layered environment | No character by default and no inexplicable lettering |
| `STORY_FRAME` | Scripted characters, setting, action and props | Camera movement or warping cannot substitute for acting |
| `EDITORIAL_MOODBOARD` | Directly requested editorial exploration | Typography permission does not transfer to production art |

## Review record

Copy `production/acceptance/art_asset_report.template.json` for each proposed canonical asset. The template is deliberately invalid (`draft`/`pending`) so an untouched file can never promote artwork. Replace every placeholder with the actual asset identity, digest, authoritative references, observations and repository-relative evidence paths. An observation must say what the reviewer examined; “looks good” is not useful evidence.

For sequences, evidence should include playback findings and frame-stepped contact sheets or overlays. For single images, include full-frame review plus useful identity, line, crop, layer or color comparisons. The validator requires evidence paths but deliberately does not assert that they exist or that their contents prove the claim. The independent reviewer and author remain accountable for those facts.

Run:

```bash
python production/validate_art_direction.py path/to/report.json
python -m unittest tests.test_art_direction -v
```

Success means the report is complete, internally consistent and promotion-eligible under contract version `1.0.0`. It does not mean a model inspected or graded the art. Promotion tooling should consume the successful JSON output and still preserve the report, evidence, approval reference and exact asset digest together.

## Failure rules

- Missing or failed required criterion: revise, do not promote.
- Missing evidence: review is incomplete.
- Creator acting as technical reviewer: invalid.
- Technical approval bound to another digest: invalid.
- No explicit author approval for the same digest: invalid.
- Rejected source asset: never repromote it; create a new revision.
- New author correction: record it as the controlling reference and review the affected asset again.
