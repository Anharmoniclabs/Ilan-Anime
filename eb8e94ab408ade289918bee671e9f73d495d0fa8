#!/usr/bin/env python3
"""Install the seven official ArtCraft Crafting Apps for Linux x86_64."""

import hashlib
import os
from pathlib import Path
import platform
import sys
import tempfile
import urllib.request


# Release URLs and SHA-256 digests from the official GitHub release metadata,
# checked on 2026-10-08. PdfCraft's release binary is named PrintCraft.
APPS = (
    ("photocraft", "PhotoCraft", "Graphics", "v0.3.0", "photocraft-0.3.0-linux-x86_64.AppImage", "29e3011f49a52ea25c8fe404258a6c5fadb02094dbb40a884d69e6ba808e6136"),
    ("vectorcraft", "VectorCraft", "Graphics", "v0.4.0", "vectorcraft-0.4.0-linux-x86_64.AppImage", "ff473f200b0103602d4e83e00bb565284d2ab03445a9ad2f76bf8ffdb302d850"),
    ("filmcraft", "FilmCraft", "AudioVideo", "v0.2.1", "filmcraft-0.2.1-linux-x86_64.AppImage", "7891c9b24c8e165a54906f8ee6a6973e051dd3c2cc1fa2729a78269fec481188"),
    ("lightcraft", "LightCraft", "Graphics", "v0.2.1", "lightcraft-0.2.1-linux-x86_64.AppImage", "c2f39adaa8a6536d5014a7ba102ff785e1a323a02e089d01db1f85378dc0fc53"),
    ("pdfcraft", "PdfCraft", "Office", "v0.2.1", "printcraft-0.2.1-linux-x86_64.AppImage", "401735c646bc5884cf1ff799d46913bce7dc3d29d06ff5a2902697e65465f584"),
    ("effectcraft", "EffectCraft", "AudioVideo", "v0.4.0", "effectcraft-0.4.0-linux-x86_64.AppImage", "994c374c54e920a12ff20fbe443199acaf49c03b30380e7a5c17b60208743d71"),
    ("designcraft", "DesignCraft", "Graphics", "v0.2.1", "designcraft-0.2.1-linux-x86_64.AppImage", "78141184d4ebc0183fe9c2609611d2a33e67668738548cc022b6778398ec8340"),
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise RuntimeError("This installer requires Linux x86_64.")

    # Check connectivity before creating installation files.
    request = urllib.request.Request("https://github.com/storytold/photocraft/releases/latest", headers={"User-Agent": "ArtCraft-suite-installer/1.0"})
    with urllib.request.urlopen(request, timeout=20):
        pass

    home = Path.home()
    app_dir = home / ".local" / "opt" / "artcraft-suite"
    bin_dir = home / ".local" / "bin"
    desktop_dir = home / ".local" / "share" / "applications"
    for directory in (app_dir, bin_dir, desktop_dir):
        directory.mkdir(parents=True, exist_ok=True)

    for repo, display_name, category, tag, asset, expected_hash in APPS:
        target = app_dir / asset
        if not (target.exists() and sha256(target) == expected_hash):
            url = f"https://github.com/storytold/{repo}/releases/download/{tag}/{asset}"
            print(f"Downloading {display_name} {tag}...", flush=True)
            fd, temporary_name = tempfile.mkstemp(prefix=f".{repo}-", dir=app_dir)
            temporary = Path(temporary_name)
            try:
                with os.fdopen(fd, "wb") as output:
                    request = urllib.request.Request(url, headers={"User-Agent": "ArtCraft-suite-installer/1.0"})
                    with urllib.request.urlopen(request, timeout=120) as response:
                        for chunk in iter(lambda: response.read(1024 * 1024), b""):
                            output.write(chunk)
                if sha256(temporary) != expected_hash:
                    raise RuntimeError(f"SHA-256 mismatch for {asset}")
                temporary.chmod(0o755)
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)

        launcher = bin_dir / repo
        launcher.write_text(
            "#!/bin/sh\n"
            "export APPIMAGE_EXTRACT_AND_RUN=1\n"
            f'exec "{target}" "$@"\n'
        )
        launcher.chmod(0o755)
        desktop = desktop_dir / f"artcraft-{repo}.desktop"
        desktop.write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={display_name}\n"
            f"Exec={launcher} %F\n"
            f"Icon=applications-{category.lower()}\n"
            f"Categories={category};\n"
            "Terminal=false\n"
        )
        print(f"Installed {display_name}: {launcher}", flush=True)

    print("All seven apps installed. Open them from the app menu or ~/.local/bin.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Install failed: {error}", file=sys.stderr)
        sys.exit(1)
