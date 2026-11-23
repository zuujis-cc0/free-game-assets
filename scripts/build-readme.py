#!/usr/bin/env python3
"""Write README.md: every pack with its previews, its downloads and a link to each of its files.

    python3 scripts/build-readme.py          # reads each pack repository's file list from GitHub's API

The files themselves live in one repository per pack (see PACKS below); this repository ties them together, keeps
the previews and the release ZIPs. Run it after a pack repository changes, then check with scripts/check.py.
Standard library only.
"""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER = "zuujiscom"
RELEASE = f"https://github.com/{OWNER}/free-game-assets/releases/download/v1.0.0"

# slug, title, pack repository, ZIP name (v1.0.0 release), size, what it holds
PACKS = [
    ("aircraft", "Aircraft models", "free-game-assets-aircraft", "zuujis-aircraft-glb", "4.2 MB",
     "24 self-contained 3D aircraft in binary glTF (GLB): airliners, business jets, fighters and classics. They open in Blender, three.js, Godot, Unity and anything else that reads GLB."),
    ("from-the-ground-up", "From the Ground Up", "free-game-assets-from-the-ground-up", "zuujis-from-the-ground-up-2d", "12.4 MB",
     "Painted city-builder art: buildings at several levels, people, props, interface icons and menu artwork."),
    ("backgrounds", "Parallax backgrounds", "free-game-assets-backgrounds", "zuujis-parallax-backgrounds", "3.6 MB",
     "Six layered parallax scenes (meadow, forest, desert, snow, city at night, alien planet) and transparent clouds."),
    ("icons", "Game icons", "free-game-assets-icons", "zuujis-game-icons", "4.5 MB",
     "128 inventory and interface icons: weapons, armour, potions, gems, food, tools, arrows. With a sprite atlas and editable vectors."),
    ("effects", "Pixel effects", "free-game-assets-effects", "zuujis-pixel-effects", "165 KB",
     "48 animated pixel effects as sprite strips: fire, ice, lightning, magic, explosions, impacts, smoke and splatters."),
    ("covenant-hall", "Covenant Hall", "free-game-assets-covenant-hall", "zuujis-covenant-hall", "17 MB",
     "30 painted building levels for a growing hall, and the four source keyframes they were made from."),
    ("tarot", "Tarot artwork", "free-game-assets-tarot", "zuujis-tarot-art", "927 MB",
     "478 Tarot card images: full decks, alternate designs, and the Rider-Waite-Smith deck in two resolutions."),
]
SCRIPTS_REPO = "zuujis-game-scripts"
SCRIPTS_ZIP = f"https://github.com/{OWNER}/free-game-assets/releases/download/v1.1.0/zuujis-game-scripts.zip"


def tree(repo):
    req = urllib.request.Request(f"https://api.github.com/repos/{OWNER}/{repo}/git/trees/main?recursive=1",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "free-game-assets-readme"})
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("truncated"):
        raise SystemExit(f"{repo}: GitHub truncated the file list")
    return sorted(t["path"] for t in data["tree"] if t["type"] == "blob" and t["path"] not in
                  ("README.md", ".gitignore"))


def blob(repo, path):
    return f"https://github.com/{OWNER}/{repo}/blob/main/{urllib.parse.quote(path)}"


def nice(name):
    stem = name.rsplit(".", 1)[0]
    return stem


def file_list(repo, files):
    """Files grouped by folder, each a link to the file on GitHub (where Download raw file saves it)."""
    groups = {}
    for p in files:
        folder, _, name = p.rpartition("/")
        groups.setdefault(folder, []).append((name, p))
    out = []
    for folder in sorted(groups, key=lambda f: (f != "", f.lower())):
        items = " · ".join(f"[{nice(n)}]({blob(repo, p)})" for n, p in sorted(groups[folder], key=lambda x: x[0].lower()))
        out.append(f"**{folder or 'Top level'}/**" if folder else "**Top level**")
        out.append("")
        out.append(items)
        out.append("")
    return "\n".join(out)


def previews(slug):
    folder = ROOT / "previews" / slug
    return sorted(p.name for p in folder.glob("*.webp"))


def pictures(slug, names, width):
    return "\n".join(f'<img src="previews/{slug}/{n}" width="{width}" alt="{slug} preview {i + 1}">'
                     for i, n in enumerate(names))


def pack_section(slug, title, repo, zipname, size, about, files):
    sheets = previews(slug)
    first, rest = sheets[:1], sheets[1:]
    lines = [
        f"## {title}",
        "",
        about,
        "",
        f"**[⬇ Download ZIP · {size}]({RELEASE}/{zipname}.zip)** · **[Every file: {repo}](https://github.com/{OWNER}/{repo})** · "
        f"[Full preview gallery](previews/{slug}/README.md)",
        "",
        "<p>",
        pictures(slug, first, "70%"),
        "</p>",
        "",
    ]
    if slug == "aircraft":
        lines += aircraft_grid(repo, files)
    if rest:
        lines += ["<details>", f"<summary>{len(rest)} more preview sheets</summary>", "", "<p>",
                  pictures(slug, rest, "49%"), "</p>", "", "</details>", ""]
    lines += ["<details>", f"<summary>All {len(files)} files, one by one</summary>", "", file_list(repo, files),
              "</details>", ""]
    return "\n".join(lines)


def aircraft_grid(repo, files):
    glbs = {p.split("/")[1]: p for p in files if p.endswith(".glb")}
    ids = sorted(p.stem for p in (ROOT / "previews" / "aircraft" / "individual").glob("*.webp"))
    rows, cells = [], []
    for i in ids:
        path = glbs.get(i)
        repo_link = f' · <a href="{blob(repo, path)}">in repo</a>' if path else ""
        cells.append(f'<td align="center"><img src="previews/aircraft/individual/{i}.webp" width="150" alt="{i}"><br>'
                     f'<b>{i.upper()}</b><br><a href="{RELEASE}/{i}.glb">GLB</a>{repo_link}</td>')
        if len(cells) == 6:
            rows.append("<tr>" + "".join(cells) + "</tr>")
            cells = []
    if cells:
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return ["<details>", "<summary>Each aircraft, with its own GLB download</summary>", "", "<table>", *rows,
            "</table>", "", "</details>", ""]


def scripts_section(files):
    js = [p for p in files if p.startswith("js/")]
    starters = [p for p in files if p.startswith("starters/")]
    assets = sorted({"/".join(p.split("/")[:2]) for p in files if p.startswith("assets/") and p.count("/") >= 2})
    lines = [
        "## Game scripts and starters",
        "",
        "Fifteen small games to start from: platformer, runner, racing in 2D and 3D, fighting, first person, flight, "
        "dungeon, match three, catch, a blank canvas, and four explorable towns. Each is one HTML file that plays with a "
        "keyboard, a gamepad or touch and fits phones upright and sideways, with the plain JavaScript libraries and the "
        "art and sound library it uses. Unzip, serve the folder, and play.",
        "",
        f"**[⬇ Download ZIP · 38 MB]({SCRIPTS_ZIP})** · **[Every file: {SCRIPTS_REPO}](https://github.com/{OWNER}/{SCRIPTS_REPO})** · "
        f"[How to use them](https://github.com/{OWNER}/{SCRIPTS_REPO}#readme)",
        "",
        '<img src="previews/game-scripts/starters.webp" width="98%" alt="Six starters: platformer, isometric town, fighting, flight, dungeon and 3D racing">',
        "",
        "<details>",
        f"<summary>The {len(starters)} starters and {len(js)} scripts, one by one</summary>",
        "",
        file_list(SCRIPTS_REPO, starters + js),
        f"**assets/**: the art and sound library the scripts read, by pack: "
        + " · ".join(f"[{a.split('/')[1]}](https://github.com/{OWNER}/{SCRIPTS_REPO}/tree/main/{urllib.parse.quote(a)})" for a in assets),
        "",
        "</details>",
        "",
    ]
    return "\n".join(lines)


def main():
    lists = {repo: tree(repo) for _, _, repo, *_ in PACKS}
    lists[SCRIPTS_REPO] = tree(SCRIPTS_REPO)
    total = sum(len(v) for k, v in lists.items() if k != SCRIPTS_REPO)
    toc = " · ".join(f"[{title}](#{title.lower().replace(' ', '-')})" for _, title, *_ in PACKS)
    table = ["| Pack | Download | Every file | Previews |", "| --- | --- | --- | --- |"]
    for slug, title, repo, zipname, size, about, in PACKS:
        table.append(f"| **[{title}](#{title.lower().replace(' ', '-')})** · {len(lists[repo])} files | "
                     f"[ZIP · {size}]({RELEASE}/{zipname}.zip) | [{repo}](https://github.com/{OWNER}/{repo}) | "
                     f"[Gallery](previews/{slug}/README.md) |")
    table.append(f"| **[Game scripts and starters](#game-scripts-and-starters)** · {len(lists[SCRIPTS_REPO])} files | "
                 f"[ZIP · 38 MB]({SCRIPTS_ZIP}) | [{SCRIPTS_REPO}](https://github.com/{OWNER}/{SCRIPTS_REPO}) | "
                 f"[Starters](#game-scripts-and-starters) |")
    head = f"""<!-- Written by scripts/build-readme.py: edit that, not this file. -->
# Zuujis free game assets

**Public-domain (CC0) art, 3D models and game starters for your games.** Use them in commercial or personal projects,
change them however you like, no credit required.

<img src="preview-aircraft.png" width="98%" alt="Four aircraft from the 3D pack">

{toc} · [Game scripts and starters](#game-scripts-and-starters) · [More CC0 assets](#more-cc0-assets) · [Licence](#licence-and-credits)

Download a whole pack as a ZIP, or take just the files you need: each pack also has its own repository where every
file can be opened and saved on its own (**Download raw file** on GitHub). {total} files in {len(PACKS)} packs.

{chr(10).join(table)}
"""
    tail = f"""## More CC0 assets

Looking for more? [MORE-CC0.md](MORE-CC0.md) lists other places with public-domain game art, 3D models, textures,
skies and sound effects (Kenney, Quaternius, KayKit, Poly Haven, ambientCG and more), checked to be CC0.

## How to help

- **Use the assets** and [tell us about your project](https://github.com/{OWNER}/free-game-assets/issues/new?template=asset-use.yml): it shows what is worth making next.
- **Report problems**: a file that will not open, a wrong preview, a broken link ([problem template](https://github.com/{OWNER}/free-game-assets/issues/new?template=problem.yml)).
- **Offer assets** you made, or CC0 work you can link the licence for: start with an [issue](https://github.com/{OWNER}/free-game-assets/issues/new?template=new-assets.yml), then see [CONTRIBUTING.md](CONTRIBUTING.md).
- **Good first issues**: [labelled ones](https://github.com/{OWNER}/free-game-assets/issues?q=is%3Aopen+label%3A%22good+first+issue%22) are small and well described.

Questions: [SUPPORT.md](SUPPORT.md). Who decides what: [GOVERNANCE.md](GOVERNANCE.md). Everyone taking part follows the
[code of conduct](CODE_OF_CONDUCT.md); report problems privately with the [form on games.zuujis.com](https://games.zuujis.com/report).

## Licence and credits

Everything in these packs is dedicated to the public domain under [CC0 1.0](LICENSE): see [CREDITS.md](CREDITS.md)
for who made what. The game scripts include three.js under its MIT licence. Aircraft names identify the subjects of
the models; CC0 does not grant trademark rights.

Using the assets in a project? [Tell us about it](https://github.com/{OWNER}/free-game-assets/issues/new?template=asset-use.yml)
(optional). [How downloads and reported use are counted](USAGE.md). Want to add assets or fix something? See
[CONTRIBUTING.md](CONTRIBUTING.md).
"""
    body = [head]
    for slug, title, repo, zipname, size, about in PACKS:
        body.append(pack_section(slug, title, repo, zipname, size, about, lists[repo]))
    body.append(scripts_section(lists[SCRIPTS_REPO]))
    body.append(tail)
    (ROOT / "README.md").write_text("\n".join(body))
    print(f"README.md: {len(PACKS)} packs, {total} files, plus {len(lists[SCRIPTS_REPO])} script and starter files")


if __name__ == "__main__":
    main()
