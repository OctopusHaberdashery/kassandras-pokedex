# Kassandra's Pokédex

An app for tracking a Pokémon card collection: every English set, with card pictures, every version
(Normal / Reverse Holo / Holo / 1st Edition…) and today's TCGplayer market prices (via tcgcsv.com).
It runs on the Android tablet and on the iPhone, and the two can share one collection.

## Install

**Android tablet:** open this link in Chrome on the tablet, then tap Install:

    https://github.com/OctopusHaberdashery/kassandras-pokedex/releases/latest/download/KassandrasPokedex.apk

**iPhone:** open this in Safari, tap the Share button, then **Add to Home Screen**:

    https://octopushaberdashery.github.io/kassandras-pokedex/

## Sharing the collection between tablet and phone

In the app: **⋮ → Share her collection between tablet & phone**, and follow the steps. It needs a GitHub key
that can only read and write gists; her collection is kept in one secret gist. Each card change carries the
time it was made, so changes from either device (even made offline) merge cleanly the next time it's online.
**Export** / **Import** in the same menu still work for a one-off copy or a backup.

## How it's built

- `android/app/src/main/assets/index.html` is the whole app (one web page).
- The website (GitHub Pages) serves that page plus `web/` (iPhone install files) and a daily copy of the prices
  made by `scripts/mirror.py`. tcgcsv doesn't let web pages download from it directly, and asks for one
  scheduled download a day, which is what this does. See `.github/workflows/website.yml`.
- The Android app (`android/`) opens the website, keeping her collection in the app's own files, and falls back
  to its built-in copy of the page when there's no internet. `.github/workflows/build.yml` builds it and
  publishes it under Releases whenever the code changes.

One-time setup for the website: **Settings → Pages → Source: GitHub Actions**.
