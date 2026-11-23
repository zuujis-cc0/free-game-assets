# Downloads and reported use

- **Downloads.** GitHub counts downloads of each release ZIP and each individual GLB. Its counts include repeat downloads, bots, and our own verification downloads. Direct downloads stay open without sign-in.
- **Use.** People can voluntarily submit a public project-use report. We count distinct reporting GitHub accounts separately from project reports. One account can use the assets in more than one project, and many people will use them without reporting back.

[Report a project using these assets](https://github.com/zuujis-cc0/free-game-assets/issues/new?template=asset-use.yml) · [Browse reported projects](https://github.com/zuujis-cc0/free-game-assets/issues?q=is%3Aissue%20label%3Aasset-use)

Run the following from a local copy of the repository to get the current per-pack and per-model download counts and both reporting totals. It uses Python 3 and GitHub's public API.

```sh
python3 scripts/stats.py
```

GitHub's release API does not tell us how many different people downloaded the ZIPs. Repository traffic counts views and clones, which measure different actions. The collection does not add tracking code to the assets or downloads.

[GitHub release asset counts](https://docs.github.com/en/rest/releases/assets) · [Repository traffic](https://github.com/zuujis-cc0/free-game-assets/graphs/traffic)
