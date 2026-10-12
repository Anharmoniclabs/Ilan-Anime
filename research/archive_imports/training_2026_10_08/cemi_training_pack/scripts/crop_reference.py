"""Extract candidate reference regions from the generated poster. Review manually before training."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
img = Image.open(root / 'references' / 'style_board.png').convert('RGB')
out = root / 'candidate_crops'
out.mkdir(exist_ok=True)
# Coordinates based on the 1536x1024 generated reference poster.
regions = {
    'portrait_01': (255, 0, 433, 318),
    'portrait_02': (434, 0, 611, 318),
    'portrait_03': (614, 0, 790, 318),
    'portrait_04': (793, 0, 967, 318),
    'portrait_05': (970, 0, 1152, 318),
    'portrait_06': (1156, 0, 1352, 318),
    'environment_01': (10, 455, 275, 593),
    'environment_02': (282, 455, 550, 593),
    'environment_03': (555, 455, 802, 593),
    'environment_04': (806, 455, 1047, 593),
    'environment_05': (1050, 455, 1278, 593),
    'environment_06': (1282, 455, 1526, 593)
}
for name, box in regions.items():
    img.crop(box).save(out / f'{name}.png')
print(f'Saved {len(regions)} candidate crops to {out}; review for text/borders before using.')
