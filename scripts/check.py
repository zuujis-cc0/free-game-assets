#!/usr/bin/env python3
"""Check the collection before it is committed or merged. Standard library only.

    python3 scripts/check.py            # every file git tracks, plus new files not ignored
    python3 scripts/check.py --quiet    # print only problems

Fails (exit 1) on anything that would make the collection harder to use or unsafe to open:
- a file type the collection does not take, a file over 10 MB, an empty file, a symlink, an unsafe or clashing name
  (two names that differ only in case break checkouts on macOS and Windows);
- a picture, model, sound or font whose contents do not match its extension or are cut short (PNG, JPEG, WebP, GIF,
  GLB, OGG, WAV, MP3, TTF/OTF), JSON that does not parse, an SVG or XML that does not parse, and an SVG with scripts,
  event handlers or links to other sites (SVGs are opened in browsers);
- a pack folder (files/<pack>/, third-party/<source>/<pack>/) without its licence, or a third-party pack missing from
  THIRD-PARTY.md;
- a link in a Markdown file to a file or folder of this repository that does not exist;
- a starter in game-scripts/ that loads a script the folder does not hold.
"""
import json
import os
import re
import struct
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_BYTES = 10 * 1024 * 1024
ALLOWED = {
    # pictures and models
    "png", "webp", "jpg", "jpeg", "gif", "svg", "glb", "gltf", "bin", "obj", "mtl", "fbx",
    # sound and fonts
    "ogg", "wav", "mp3", "ttf", "otf",
    # data, docs and the game scripts
    "json", "xml", "tmx", "tsx", "txt", "md", "html", "js", "css", "yml", "yaml", "py", "sh", "vectorcraft",
}
NO_EXTENSION = {"LICENSE", ".gitignore"}
SAFE_NAME = re.compile(r"^[A-Za-z0-9 _.,()&+'\[\]#@!-]+$")


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                         cwd=ROOT, capture_output=True, check=True).stdout
    return sorted({p for p in out.decode().split("\0") if p and (ROOT / p).exists() or (p and (ROOT / p).is_symlink())})


class Problems(list):
    def add(self, path, text):
        self.append(f"{path}: {text}")


# ---- file contents -------------------------------------------------------------------------------------------------

def check_png(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or data[12:16] != b"IHDR":
        return "not a PNG"
    w, h = struct.unpack(">II", data[16:24])
    if not w or not h:
        return "PNG with no size"
    if b"IEND" not in data[-16:]:
        return "PNG cut short (no IEND)"


def check_jpeg(data):
    if not data.startswith(b"\xff\xd8"):
        return "not a JPEG"
    if b"\xff\xd9" not in data[-64:]:
        return "JPEG cut short (no end marker)"


def check_webp(data):
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return "not a WebP"
    if struct.unpack("<I", data[4:8])[0] + 8 > len(data):
        return "WebP cut short"


def check_gif(data):
    if data[:6] not in (b"GIF87a", b"GIF89a"):
        return "not a GIF"


def check_glb(data):
    if data[:4] != b"glTF":
        return "not a GLB (binary glTF)"
    version, length = struct.unpack("<II", data[4:12])
    if version != 2:
        return f"glTF version {version}, expected 2"
    if length != len(data):
        return f"GLB says {length} bytes but the file has {len(data)}"
    chunk_len, chunk_type = struct.unpack("<II", data[12:20])
    if chunk_type != 0x4E4F534A:
        return "GLB's first chunk is not JSON"
    try:
        gltf = json.loads(data[20:20 + chunk_len])
    except ValueError as e:
        return f"GLB JSON does not parse: {e}"
    for buf in gltf.get("buffers", []):
        if "uri" in buf and not buf["uri"].startswith("data:"):
            return "GLB points to an outside file (should be self-contained)"


def check_ogg(data):
    if data[:4] != b"OggS":
        return "not an Ogg file"


def check_wav(data):
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return "not a WAV"


def check_mp3(data):
    if not (data[:3] == b"ID3" or (data[0] == 0xFF and data[1] & 0xE0 == 0xE0)):
        return "not an MP3"


def check_font(data):
    if data[:4] not in (b"\x00\x01\x00\x00", b"OTTO", b"true"):
        return "not a TrueType/OpenType font"


def check_json(data):
    try:
        json.loads(data.decode("utf-8-sig"))
    except (ValueError, UnicodeDecodeError) as e:
        return f"JSON does not parse: {e}"


def check_xml(data):
    try:
        ET.fromstring(data)
    except ET.ParseError as e:
        return f"XML does not parse: {e}"


def check_svg(data):
    bad = check_xml(data)
    if bad:
        return bad.replace("XML", "SVG")
    root = ET.fromstring(data)
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1].lower()
        if tag in ("script", "foreignobject", "iframe", "embed", "object"):
            return f"SVG contains <{tag}>"
        for name, value in el.attrib.items():
            local = name.rsplit("}", 1)[-1].lower()
            if local.startswith("on"):
                return f"SVG has an event handler ({local})"
            if local == "href" and value.strip() and not value.strip().startswith(("#", "data:image/")):
                return f"SVG links to {value[:60]}"


CHECKS = {"png": check_png, "jpg": check_jpeg, "jpeg": check_jpeg, "webp": check_webp, "gif": check_gif,
          "glb": check_glb, "ogg": check_ogg, "wav": check_wav, "mp3": check_mp3, "ttf": check_font,
          "otf": check_font, "json": check_json, "gltf": check_json, "xml": check_xml, "tmx": check_xml,
          "tsx": check_xml, "svg": check_svg}


# ---- the collection's own rules --------------------------------------------------------------------------------------

def check_files(files, problems):
    seen = {}
    for rel in files:
        path = ROOT / rel
        name = path.name
        if path.is_symlink():
            problems.add(rel, "symlinks are not allowed")
            continue
        if not SAFE_NAME.match(name) or name.startswith("-") or name.endswith((" ", ".")):
            problems.add(rel, "use letters, digits, spaces and - _ . ( ) in file names")
        low = rel.lower()
        if low in seen:
            problems.add(rel, f"differs from {seen[low]} only in upper/lower case")
        seen[low] = rel
        ext = name.rsplit(".", 1)[-1].lower() if "." in name.lstrip(".") else ""
        if not ext and name not in NO_EXTENSION:
            problems.add(rel, "file has no extension")
        elif ext and ext not in ALLOWED:
            problems.add(rel, f".{ext} files are not taken (see CONTRIBUTING.md)")
        size = path.stat().st_size
        if size > MAX_BYTES:
            problems.add(rel, f"{size / 1e6:.1f} MB is over the 10 MB limit")
            continue
        if size == 0:
            problems.add(rel, "empty file")
            continue
        check = CHECKS.get(ext)
        if check:
            bad = check(path.read_bytes())
            if bad:
                problems.add(rel, bad)


def has_licence(folder, files):
    prefix = folder + "/"
    return any(f.startswith(prefix) and "/" not in f[len(prefix):]
               and re.match(r"(?i)^(licen[cs]e|copying)", f[len(prefix):]) for f in files)


def check_packs(files, problems):
    packs = sorted({"/".join(f.split("/")[:2]) for f in files if f.startswith("files/") and f.count("/") >= 2})
    for pack in packs:
        if not has_licence(pack, files):
            problems.add(pack, "pack has no LICENSE file")
        if not any(f == pack + "/CREDITS.md" for f in files):
            problems.add(pack, "pack has no CREDITS.md")
    credits = (ROOT / "THIRD-PARTY.md").read_text() if (ROOT / "THIRD-PARTY.md").exists() else ""
    third = sorted({"/".join(f.split("/")[:3]) for f in files if f.startswith("third-party/") and f.count("/") >= 3})
    for pack in third:
        if not has_licence(pack, files) and not (ROOT / pack / "SOURCE.md").exists():
            problems.add(pack, "third-party pack has neither the creator's licence file nor a SOURCE.md")
        if f"({pack}/)" not in credits and f"({urllib.parse.quote(pack)}/)" not in credits:
            problems.add(pack, "third-party pack is not credited in THIRD-PARTY.md (link it as (" + pack + "/))")


LINK = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def check_links(files, problems):
    known = set(files)
    folders = {"/".join(f.split("/")[:i]) for f in files for i in range(1, f.count("/") + 1)}
    for rel in files:
        if not rel.endswith(".md"):
            continue
        base = os.path.dirname(rel)
        text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        for target in LINK.findall(text):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                continue
            path = urllib.parse.unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not path:
                continue
            full = os.path.normpath(os.path.join(base, path)).replace(os.sep, "/").rstrip("/")
            if full.startswith(".."):
                problems.add(rel, f"link leaves the repository: {target}")
            elif full not in known and full not in folders:
                problems.add(rel, f"broken link: {target}")


def check_starters(files, problems):
    for rel in files:
        if not (rel.startswith("game-scripts/starters/") and rel.endswith(".html")):
            continue
        html = (ROOT / rel).read_text(encoding="utf-8")
        for p in re.findall(r'"(/js/[A-Za-z0-9./-]+\.js)"', html):
            if "game-scripts" + p not in files:
                problems.add(rel, f"loads {p}, which game-scripts/ does not hold")
        for p in re.findall(r"three/addons/([A-Za-z/]+\.js)", html):
            if f"game-scripts/js/three-addons/{p}" not in files:
                problems.add(rel, f"imports three/addons/{p}, which game-scripts/ does not hold")


def main():
    quiet = "--quiet" in sys.argv
    files = tracked_files()
    problems = Problems()
    check_files(files, problems)
    check_packs(files, problems)
    check_links(files, problems)
    check_starters(files, problems)
    for p in problems:
        print(p)
    if problems:
        print(f"\n{len(problems)} problem(s) in {len(files)} files.", file=sys.stderr)
        return 1
    if not quiet:
        print(f"OK: {len(files)} files checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
