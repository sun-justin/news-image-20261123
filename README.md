# news-image-20261123

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/sun-justin/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/sun-justin/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

A program that draws a newspaper front page summing up the world news
of Monday 23 November 2026, as a 1024x1024 PNG.

## What it draws

**THE WORLD TODAY — Monday 23 November 2026**, a front page with
37 stories across 9 regions:

- Lead: COP31 climate talks in Antalya collapse with no deal after
  the EU rejects a draft that never mentions fossil fuels.
- Iran strikes a US base in Bahrain and two tankers are hit in the
  Strait of Hormuz; Gulf states condemn the attacks.
- A Russian drone hits flats in Dymer near Kyiv: 2 killed, 14 missing.
- A dotted world map marking the day's datelines, from Sinaloa to
  Sydney, and BepiColombo entering orbit around Mercury after an
  eight-year voyage.
- Briefs: the AI sell-off and S&P 500 correction; Mexico captures
  "El Chapo Isidro"; 50 missing in the Banten factory fire; NATO to
  meet over missiles hitting Poland; Nepal's PM meets Modi in Delhi;
  South Korea's education minister quits in an AI-cheating scandal;
  India post a record 720/9 in Wellington; and 27 more.
- A markets strip: S&P 500 6,910, Nasdaq 22,618, Dow 48,147,
  Brent $92.57, gold $3,538 (Friday closes).

## How it works

`main.py` is pure Python 3 standard library. It draws every pixel
itself — a hand-built stroke font with serif feet, shaded
illustrations, a dotted world map, and a hand-written PNG encoder
(`zlib` + `struct`) — with no network, no clock and no randomness.
The page is rendered at 2x and downsampled for clean edges, so two
runs write byte-identical output.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

The image is written to `out/entry.png` (1024x1024, under 1 MiB).
