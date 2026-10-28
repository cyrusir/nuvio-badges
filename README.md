# Nuvio badges (from paulthery/aiostreams-badges)

The 70 AIOStreams badges by paulthery, rebuilt for Nuvio's stream badges.

    icons/                       70 PNGs, 128 px high (frame and corners baked in)
    nuvio-badges.json            Nuvio badge import (groups + filters)
    formatter/description-nuvio.txt   AIOStreams description template (optional, see below)
    formatter/name.txt, name-alt.txt  unchanged from the original repo
    preview.png                  how they look in a Nuvio stream list

## Why images for everything

Nuvio only draws image badges (no text badges, no custom CSS). Each badge is
shown in a 16dp slot, 34–92dp wide, clipped to a 6dp radius, so every PNG is
at least 34:16 wide and uses that radius. Colours, Inter type and the
two-line codec / dynamic range design follow the original.

## Install

1. Host this folder: create a public GitHub repo (for example `nuvio-badges`)
   and upload everything in it.
2. In `nuvio-badges.json`, replace `YOUR-GITHUB-NAME` with your GitHub user
   name (find and replace, 70 image URLs). If your repo or branch has another
   name, change `nuvio-badges/main` too.
3. Nuvio: Settings > Streams > Fusion badge URLs (TV: Settings > Layout >
   Streams), paste the raw URL
   `https://raw.githubusercontent.com/YOUR-GITHUB-NAME/nuvio-badges/main/nuvio-badges.json`
   and press Import.

## Formatter (optional, for 11 badges)

Nuvio matches badge patterns against the file name, the stream name and the
description, not AIOStreams' parsed fields. Resolution, source, HDR, audio,
channels, codec, 10-bit, editions and the French file-name tags work from the
file name alone.

T1 T2 T3 LQ, RD TB AD EN, VF (French audio) and VO need AIOStreams' results.
`description-nuvio.txt` is the original description template with invisible
markers appended for those. In AIOStreams: Formatter > Custom > Description
Template, paste the whole file (copy from the raw file so the invisible
characters come along), save. `name.txt` goes in Name Template as before.

- Tiers: add the Vidhin05 English expressions to Ranked Stream Expressions,
  as in the original INSTALL.md.
- Services: no ranked expressions needed any more; the template reads the
  cached service directly.

## Differences from the AIOStreams version

- Nuvio shows every matching badge, so group order (HDR+DV before HDR10+,
  ATMOS before TRUEHD, first edition wins, …) is built into the patterns.
- Editions come from the file name, so a release named "Extended" gets the
  badge. Uncut Gems and The Final Cut (2004) are excluded by name.
- After replacing an image, bump `?v=1` in the JSON and re-import.
