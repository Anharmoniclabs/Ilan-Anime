"""Reference-locked image manifests and editable Blender scene generation."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import shutil

from PIL import Image

from studio.paths import write_json

SCHEMA_VERSION = 1
CAMERA_MODES = {"orthographic", "perspective"}
WORKFLOWS = {"camera_locked", "2.5d", "authored_3d"}
LAYER_MODES = {"backplate", "flat", "card", "mesh"}
MANIFEST_NAME = "manifest.json"


class ReferenceLockError(ValueError):
    """Raised when a reference-lock manifest or source asset is invalid."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _positive_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ReferenceLockError(f"{label} must be a positive integer")


def _asset_path(base: Path, value, label) -> Path:
    if not isinstance(value, str) or not value:
        raise ReferenceLockError(f"{label} must be a relative asset path")
    path = Path(value)
    if path.is_absolute():
        raise ReferenceLockError(f"{label} must be relative to the manifest directory")
    resolved = (base / path).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError as exc:
        raise ReferenceLockError(f"{label} escapes the manifest directory") from exc
    if not resolved.is_file():
        raise ReferenceLockError(f"missing {label}: {value}")
    return resolved


def _image_size(path: Path, label) -> tuple[int, int]:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            return image.size
    except (OSError, ValueError) as exc:
        raise ReferenceLockError(f"invalid {label} image: {path}") from exc


def _read_manifest(path):
    path = Path(path).resolve()
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReferenceLockError(f"cannot read manifest: {path}") from exc
    if not isinstance(manifest, dict):
        raise ReferenceLockError("manifest must be a JSON object")
    return path, manifest


def init(image, out, *, camera="orthographic", width=None, height=None):
    """Create a source-copying, camera-locked manifest and a usage README."""
    source_path, out = Path(image).resolve(), Path(out).resolve()
    if camera not in CAMERA_MODES:
        raise ReferenceLockError(f"camera must be one of {sorted(CAMERA_MODES)}")
    if not source_path.is_file():
        raise ReferenceLockError(f"missing source image: {source_path}")
    if (width is None) != (height is None):
        raise ReferenceLockError("--width and --height must be supplied together")

    source_size = _image_size(source_path, "source")
    source_width, source_height = source_size
    render_width = source_width if width is None else width
    render_height = source_height if height is None else height
    _positive_int(render_width, "width")
    _positive_int(render_height, "height")
    if render_width * source_height != render_height * source_width:
        raise ReferenceLockError("render width and height must preserve the source image aspect ratio")

    out.mkdir(parents=True, exist_ok=True)
    if (out / MANIFEST_NAME).exists() or (out / "README.md").exists():
        raise ReferenceLockError(f"refusing to overwrite an existing reference-lock project: {out}")
    assets_dir = out / "assets"
    assets_dir.mkdir(exist_ok=True)
    asset_path = assets_dir / source_path.name
    source_digest = _sha256(source_path)
    if asset_path.exists():
        if not asset_path.is_file() or _sha256(asset_path) != source_digest:
            raise ReferenceLockError(f"refusing to overwrite a different asset: {asset_path}")
    else:
        shutil.copyfile(source_path, asset_path)
    relative_asset = asset_path.relative_to(out).as_posix()

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "workflow": "camera_locked",
        "source": {
            "path": relative_asset,
            "sha256": source_digest,
            "width": source_width,
            "height": source_height,
            "provenance": {"method": "copied", "original_filename": source_path.name},
        },
        "camera": {"mode": camera, "locked": True},
        "render": {"width": render_width, "height": render_height, "fps": 24},
        "layers": [{
            "id": "reference",
            "image": relative_asset,
            "image_sha256": source_digest,
            "depth": 0.0,
            "parallax": 0.0,
            "mode": "backplate",
            "approved": True,
        }],
    }
    manifest_path = write_json(out / MANIFEST_NAME, manifest)
    _write_readme(out, source_path, manifest_path)
    return {"manifest": str(manifest_path), "source": relative_asset, "sha256": source_digest,
            "dimensions": [source_width, source_height], "camera": camera}


def _write_readme(out, original_image, manifest_path):
    script_path = out / "reference_lock.py"
    manifest_path = manifest_path.resolve()
    text = f"""# Reference-locked Blender scene

This project reproduces the supplied 2D source from one fixed camera; it does
not reconstruct hidden geometry. The default `camera_locked` workflow is
visually faithful only from the reference camera.

## Exact commands

Run from the repository root:

```bash
python -m studio reference-lock validate "{manifest_path}"
python -m studio reference-lock blender-script "{manifest_path}" --out "{script_path.resolve()}"
blender -b --python "{script_path.resolve()}"
```

The last command creates `{script_path.stem}.blend`, an editable Blender scene.
The source image was copied to `assets/{Path(original_image).name}`; its
SHA-256, dimensions, and original filename are recorded in `manifest.json`.

## Beyond the reference view

Use user-authored, registered image layers with masks and explicit depth planes
for 2.5D parallax; separate foreground, window, reflection, and rain only with
approved masks. Use authored meshes for new camera angles. Never infer or
generate unseen geometry from this single image. 2.5D reveals can expose holes,
and a single view cannot provide exact hidden sides or arbitrary new angles.
Layer depths are ordered back-to-front. Set `workflow` to `2.5d`, choose a
perspective camera, and author at least two image layers with nonzero parallax
before generating a parallax scene. Mesh layers require a user-authored `.blend`
file and object name in the layer's `mesh` and `mesh_object` fields.

Generated or modified assets remain exploratory until technically reviewed and
Luis approves the exact file. No paid generation is used by this workflow.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def validate(manifest_path):
    """Verify schema, source and layer hashes, dimensions, modes, and depth order."""
    path, manifest = _read_manifest(manifest_path)
    base = path.parent
    if isinstance(manifest.get("schema_version"), bool) or manifest.get("schema_version") != SCHEMA_VERSION:
        raise ReferenceLockError(f"schema_version must be {SCHEMA_VERSION}")
    workflow = manifest.get("workflow")
    if not isinstance(workflow, str) or workflow not in WORKFLOWS:
        raise ReferenceLockError(f"workflow must be one of {sorted(WORKFLOWS)}")

    source = manifest.get("source")
    if not isinstance(source, dict):
        raise ReferenceLockError("source must be an object")
    source_path = _asset_path(base, source.get("path"), "source.path")
    for key in ("width", "height"):
        _positive_int(source.get(key), f"source.{key}")
    source_digest = source.get("sha256")
    if not isinstance(source_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", source_digest):
        raise ReferenceLockError("source.sha256 must be a lowercase SHA-256 digest")
    actual_digest = _sha256(source_path)
    if actual_digest != source_digest:
        raise ReferenceLockError("source SHA-256 mismatch")
    source_dimensions = _image_size(source_path, "source")
    if source_dimensions != (source["width"], source["height"]):
        raise ReferenceLockError("source image dimensions do not match the manifest")
    provenance = source.get("provenance")
    if (not isinstance(provenance, dict) or provenance.get("method") != "copied"
            or not isinstance(provenance.get("original_filename"), str)
            or not provenance["original_filename"]):
        raise ReferenceLockError("source.provenance must record the copied source filename")

    camera = manifest.get("camera")
    if not isinstance(camera, dict) or not isinstance(camera.get("mode"), str) or camera["mode"] not in CAMERA_MODES:
        raise ReferenceLockError(f"camera.mode must be one of {sorted(CAMERA_MODES)}")
    if not isinstance(camera.get("locked"), bool):
        raise ReferenceLockError("camera.locked must be a boolean")
    if workflow == "camera_locked" and camera["locked"] is not True:
        raise ReferenceLockError("camera_locked workflow requires a locked camera")
    if workflow == "2.5d" and (camera["mode"] != "perspective" or camera["locked"]):
        raise ReferenceLockError("2.5d workflow requires an unlocked perspective camera")

    render = manifest.get("render")
    if not isinstance(render, dict):
        raise ReferenceLockError("render must be an object")
    for key in ("width", "height", "fps"):
        _positive_int(render.get(key), f"render.{key}")
    if render["width"] * source["height"] != render["height"] * source["width"]:
        raise ReferenceLockError("render dimensions must preserve the source image aspect ratio")
    if render["fps"] != 24:
        raise ReferenceLockError("render.fps must be 24")

    layers = manifest.get("layers")
    if not isinstance(layers, list) or not layers:
        raise ReferenceLockError("layers must be a nonempty array")
    ids, depths = set(), []
    mesh_layers = 0
    nonzero_parallax = False
    for index, layer in enumerate(layers):
        if not isinstance(layer, dict):
            raise ReferenceLockError(f"layers[{index}] must be an object")
        for key in ("id", "image", "depth", "parallax", "mode", "approved"):
            if key not in layer:
                raise ReferenceLockError(f"layers[{index}] is missing {key}")
        layer_id = layer["id"]
        if not isinstance(layer_id, str) or not layer_id:
            raise ReferenceLockError(f"layers[{index}].id must be a nonempty string")
        if layer_id in ids:
            raise ReferenceLockError(f"duplicate layer id: {layer_id}")
        ids.add(layer_id)
        if not isinstance(layer["mode"], str) or layer["mode"] not in LAYER_MODES:
            raise ReferenceLockError(f"invalid layer mode: {layer['mode']}")
        if not isinstance(layer["approved"], bool):
            raise ReferenceLockError(f"layers[{index}].approved must be a boolean")
        depth = layer["depth"]
        parallax = layer["parallax"]
        if isinstance(depth, bool) or not isinstance(depth, (int, float)) or not math.isfinite(depth):
            raise ReferenceLockError(f"layers[{index}].depth must be finite")
        if isinstance(parallax, bool) or not isinstance(parallax, (int, float)) or not math.isfinite(parallax):
            raise ReferenceLockError(f"layers[{index}].parallax must be finite")
        depths.append(depth)
        nonzero_parallax |= parallax != 0

        layer_image = _asset_path(base, layer["image"], f"layers[{index}].image")
        image_digest = layer.get("image_sha256")
        if not isinstance(image_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", image_digest):
            raise ReferenceLockError(f"layers[{index}].image_sha256 must be a lowercase SHA-256 digest")
        if _sha256(layer_image) != image_digest:
            raise ReferenceLockError(f"layer image SHA-256 mismatch: {layer_id}")
        layer_size = _image_size(layer_image, f"layers[{index}].image")
        if layer_size != source_dimensions:
            raise ReferenceLockError(f"layer image dimensions do not match the source: {layer_id}")

        mask_value = layer.get("mask")
        if mask_value is not None:
            mask_path = _asset_path(base, mask_value, f"layers[{index}].mask")
            mask_digest = layer.get("mask_sha256")
            if not isinstance(mask_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", mask_digest):
                raise ReferenceLockError(f"layers[{index}].mask_sha256 must be a lowercase SHA-256 digest")
            if _sha256(mask_path) != mask_digest:
                raise ReferenceLockError(f"layer mask SHA-256 mismatch: {layer_id}")
            if _image_size(mask_path, f"layers[{index}].mask") != layer_size:
                raise ReferenceLockError(f"layer mask dimensions do not match its image: {layer_id}")
        elif "mask_sha256" in layer:
            raise ReferenceLockError(f"layers[{index}].mask_sha256 is set without a mask")

        if layer["mode"] == "mesh":
            mesh_layers += 1
            mesh_path = _asset_path(base, layer.get("mesh"), f"layers[{index}].mesh")
            mesh_digest = layer.get("mesh_sha256")
            if not isinstance(mesh_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", mesh_digest):
                raise ReferenceLockError(f"layers[{index}].mesh_sha256 must be a lowercase SHA-256 digest")
            if _sha256(mesh_path) != mesh_digest:
                raise ReferenceLockError(f"authored mesh SHA-256 mismatch: {layer_id}")
            if not mesh_path.suffix.lower() == ".blend":
                raise ReferenceLockError(f"layers[{index}].mesh must reference a Blender .blend file")
            if not isinstance(layer.get("mesh_object"), str) or not layer["mesh_object"]:
                raise ReferenceLockError(f"layers[{index}].mesh_object must name an authored object")
        elif any(key in layer for key in ("mesh", "mesh_sha256", "mesh_object")):
            raise ReferenceLockError(f"layers[{index}] mesh asset fields require mode 'mesh'")

    if any(after <= before for before, after in zip(depths, depths[1:])):
        raise ReferenceLockError("layer depths must be unique and ordered back-to-front (ascending)")
    if workflow == "camera_locked":
        if len(layers) != 1 or layers[0]["mode"] != "backplate" or layers[0]["parallax"] != 0:
            raise ReferenceLockError("camera_locked requires exactly one backplate at parallax 0")
        if not layers[0]["approved"]:
            raise ReferenceLockError("camera_locked backplate must be approved")
        if layers[0]["image"] != source["path"] or layers[0]["image_sha256"] != source_digest:
            raise ReferenceLockError("camera_locked backplate must be the verified source image")
    elif workflow == "2.5d":
        if len(layers) < 2 or not nonzero_parallax:
            raise ReferenceLockError("2.5d requires at least two explicit layers and nonzero parallax")
    elif workflow == "authored_3d" and mesh_layers == 0:
        raise ReferenceLockError("authored_3d requires at least one user-authored mesh layer")
    elif workflow == "authored_3d" and camera["locked"]:
        raise ReferenceLockError("authored_3d requires an unlocked camera for new angles")

    return {"valid": True, "manifest": str(path), "workflow": workflow,
            "layers": len(layers), "source_sha256": source_digest}


def blender_script(manifest_path, out):
    """Write a standalone Blender Python script for the validated manifest."""
    result = validate(manifest_path)
    manifest_path = Path(manifest_path).resolve()
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    script = _BLENDER_SCRIPT.replace("__MANIFEST_PATH__", repr(str(manifest_path)))
    out.write_text(script, encoding="utf-8")
    return {"script": str(out), "manifest": result["manifest"], "layers": result["layers"]}


_BLENDER_SCRIPT = r'''"""Generated by `python -m studio reference-lock blender-script`."""
import hashlib
import json
from pathlib import Path

import bpy

MANIFEST_PATH = Path(__MANIFEST_PATH__)
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
asset_root = MANIFEST_PATH.parent


def verify(path, expected, label):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    if digest.hexdigest() != expected:
        raise RuntimeError(label + " SHA-256 changed after manifest validation")


def asset(value, digest, label):
    path = (asset_root / value).resolve()
    try:
        path.relative_to(asset_root.resolve())
    except ValueError:
        raise RuntimeError(label + " escapes the manifest directory")
    if not path.is_file():
        raise RuntimeError("Missing " + label + ": " + str(path))
    verify(path, digest, label)
    return path


source = manifest["source"]
source_path = asset(source["path"], source["sha256"], "source image")
for layer in manifest["layers"]:
    asset(layer["image"], layer["image_sha256"], "layer image " + layer["id"])
    if layer.get("mask"):
        asset(layer["mask"], layer["mask_sha256"], "layer mask " + layer["id"])
    if layer["mode"] == "mesh":
        asset(layer["mesh"], layer["mesh_sha256"], "authored mesh " + layer["id"])

scene = bpy.context.scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.materials):
    for datablock in list(datablocks):
        if datablock.users == 0:
            datablocks.remove(datablock)

engine = None
for candidate in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = candidate
        engine = candidate
        break
    except (TypeError, ValueError):
        continue
if engine is None:
    raise RuntimeError("This Blender build has neither EEVEE engine identifier")

scene.render.resolution_x = manifest["render"]["width"]
scene.render.resolution_y = manifest["render"]["height"]
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.render.fps_base = 1.0
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "8"
scene.view_settings.view_transform = "Standard"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
if hasattr(scene.view_settings, "look"):
    scene.view_settings.look = "None"

camera_data = bpy.data.cameras.new("Reference Locked Camera")
camera = bpy.data.objects.new("Reference Locked Camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera.location = (0.0, 0.0, 0.0)
camera.rotation_euler = (0.0, 0.0, 0.0)
camera_data.clip_start = 0.01
camera_data.clip_end = 10000.0
camera_distance = 100.0
if manifest["camera"]["mode"] == "orthographic":
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = manifest["source"]["width"]
else:
    camera_data.type = "PERSP"
    camera_data.lens = 50.0
    camera_data.sensor_width = 36.0
    camera_data.sensor_fit = "HORIZONTAL"
if manifest["workflow"] == "camera_locked":
    camera.lock_location = (True, True, True)
    camera.lock_rotation = (True, True, True)
camera["reference_lock"] = True
camera["projection"] = manifest["camera"]["mode"]


def image_material(layer):
    image_path = asset(layer["image"], layer["image_sha256"], "layer image " + layer["id"])
    image = bpy.data.images.load(str(image_path), check_existing=True)
    if hasattr(image, "colorspace_settings"):
        try:
            image.colorspace_settings.name = "sRGB"
        except TypeError:
            pass
    material = bpy.data.materials.new("Reference " + layer["id"])
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    links.new(texture.outputs["Color"], emission.inputs["Color"])
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    alpha_output = texture.outputs["Alpha"]
    if layer.get("mask"):
        mask_path = asset(layer["mask"], layer["mask_sha256"], "layer mask " + layer["id"])
        mask_image = bpy.data.images.load(str(mask_path), check_existing=True)
        mask_texture = nodes.new("ShaderNodeTexImage")
        mask_texture.image = mask_image
        mask_texture.image.colorspace_settings.name = "Non-Color"
        rgb_to_bw = nodes.new("ShaderNodeRGBToBW")
        multiply = nodes.new("ShaderNodeMath")
        multiply.operation = "MULTIPLY"
        links.new(mask_texture.outputs["Color"], rgb_to_bw.inputs["Color"])
        links.new(alpha_output, multiply.inputs[0])
        links.new(rgb_to_bw.outputs["Val"], multiply.inputs[1])
        alpha_output = multiply.outputs["Value"]
    links.new(alpha_output, mix.inputs[0])
    links.new(mix.outputs["Shader"], output.inputs["Surface"])
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    elif hasattr(material, "blend_method"):
        material.blend_method = "BLEND"
    return material


def add_image_plane(layer):
    depth = float(layer["depth"])
    distance = camera_distance - depth
    if distance <= 0.01:
        raise RuntimeError("Layer depth places the image at or behind the camera: " + layer["id"])
    image_width = manifest["source"]["width"]
    image_height = manifest["source"]["height"]
    if camera_data.type == "ORTHO":
        plane_width = float(image_width)
        plane_height = float(image_height)
    else:
        plane_width = distance * camera_data.sensor_width / camera_data.lens
        plane_height = plane_width * image_height / image_width
    vertices = [(-plane_width / 2, -plane_height / 2, 0),
                (plane_width / 2, -plane_height / 2, 0),
                (plane_width / 2, plane_height / 2, 0),
                (-plane_width / 2, plane_height / 2, 0)]
    mesh = bpy.data.meshes.new("Reference plane " + layer["id"])
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for loop, coord in zip(mesh.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[loop.index].uv = coord
    obj = bpy.data.objects.new("Reference " + layer["id"], mesh)
    scene.collection.objects.link(obj)
    obj.location = (0.0, 0.0, -distance)
    obj.data.materials.append(image_material(layer))
    obj["reference_lock_id"] = layer["id"]
    obj["mode"] = layer["mode"]
    obj["depth"] = depth
    obj["parallax"] = float(layer["parallax"])
    if not layer["approved"] or (manifest["workflow"] == "authored_3d" and layer["mode"] == "backplate"):
        obj.hide_render = True
    return obj


for layer in manifest["layers"]:
    if layer["mode"] == "mesh":
        mesh_file = asset(layer["mesh"], layer["mesh_sha256"], "authored mesh " + layer["id"])
        with bpy.data.libraries.load(str(mesh_file), link=False) as (data_from, data_to):
            object_name = layer["mesh_object"]
            if object_name not in data_from.objects:
                raise RuntimeError("Authored mesh object not found: " + object_name)
            data_to.objects = [object_name]
        imported = next((obj for obj in data_to.objects if obj is not None), None)
        if imported is None:
            raise RuntimeError("Could not load authored mesh object: " + object_name)
        scene.collection.objects.link(imported)
        imported["reference_lock_id"] = layer["id"]
        imported["mode"] = "mesh"
        imported["depth"] = float(layer["depth"])
        imported["parallax"] = float(layer["parallax"])
        if not layer["approved"]:
            imported.hide_render = True
    else:
        add_image_plane(layer)

scene.render.filepath = str(MANIFEST_PATH.parent / "render.png")
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).resolve().with_suffix(".blend")))
print("Saved editable reference-locked scene:", Path(__file__).resolve().with_suffix(".blend"))
'''
