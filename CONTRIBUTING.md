# Contributing

Thanks for helping. This collection only works if everything in it is safe for anyone to use, so the rules below are
mostly about licences and about files that open cleanly everywhere.

## How the collection is laid out

- **This repository** ([free-game-assets](https://github.com/zuujis-cc0/free-game-assets)) ties everything together:
  the README, the preview galleries in [previews/](previews/README.md), the licence and credits, the checks in
  [scripts/](scripts/), and the ZIP downloads on the [releases page](https://github.com/zuujis-cc0/free-game-assets/releases).
- **Each pack's files** live in a repository of their own, so this one stays quick to clone:
  [aircraft](https://github.com/zuujis-cc0/free-game-assets-aircraft) ·
  [from-the-ground-up](https://github.com/zuujis-cc0/free-game-assets-from-the-ground-up) ·
  [backgrounds](https://github.com/zuujis-cc0/free-game-assets-backgrounds) ·
  [icons](https://github.com/zuujis-cc0/free-game-assets-icons) ·
  [effects](https://github.com/zuujis-cc0/free-game-assets-effects) ·
  [covenant-hall](https://github.com/zuujis-cc0/free-game-assets-covenant-hall) ·
  [tarot](https://github.com/zuujis-cc0/free-game-assets-tarot) ·
  [game scripts and starters](https://github.com/zuujis-cc0/zuujis-game-scripts).

Fixing or improving a file in a pack: open the pull request on that pack's repository. Previews, the README, the
credits or the checks: open it here.

## Offering new assets

1. **Open an issue first** with the [New assets template](https://github.com/zuujis-cc0/free-game-assets/issues/new?template=new-assets.yml),
   so we can agree on where the files go before you do the work. Small fixes need no issue.
2. **Only what you have the right to give.** Your own work, or work already under CC0 whose source you can link.
   No AI output from services whose terms limit how it may be used, no ripped game assets, no fan art of other
   people's characters, logos or brands.
3. **Everything here is CC0.** By opening a pull request you dedicate your contribution to the public domain under
   [CC0 1.0](LICENSE). Say in the pull request who made the files, and for CC0 work by others, link the page that
   states its licence; we add it to [CREDITS.md](CREDITS.md).
4. **Files that open everywhere.** PNG or WebP for pictures (JPEG for photos and large paintings), GLB for 3D models
   (self-contained: textures inside), OGG or WAV for sounds, TTF or OTF for fonts, JSON for data. No file over 10 MB.
   Plain file names: letters, digits, spaces and `- _ . ( )`. SVGs may not contain scripts or links.
5. **Add previews.** New sprites or models get a contact sheet in `previews/<pack>/` (WebP, about 760 px wide, like
   the existing ones) and a line in that pack's gallery README.

## Before you open a pull request

```sh
python3 scripts/check.py                 # file types, sizes, damaged files, licences, broken links
python3 scripts/build-readme.py          # after a pack repository changed: rewrites README.md
```

Both use Python 3 and nothing else. The same check runs on every pull request; a pull request merges only when it passes.
In the game scripts repository, `python3 scripts/smoke.py` plays every starter in headless Firefox.

## Reporting a problem

A file that will not open, looks wrong, or a licence question: use the
[Problem template](https://github.com/zuujis-cc0/free-game-assets/issues/new?template=problem.yml). If you think
something here is not ours to give away, say so there and we will take it down while we look.

Please follow the [code of conduct](CODE_OF_CONDUCT.md).
