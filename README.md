# news-image-20261123

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/sun-justin/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/sun-justin/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

A program that draws a newspaper front page summing up the world news
of Monday 23 November 2026, as a 1024x1024 PNG.

## What it draws

**THE WORLD TODAY — Monday 23 November 2026**, a front page with
37 dated stories across 9 regions:

- Lead: COP31 climate talks in Antalya collapse as the EU rejects a
  final draft that never mentions fossil fuels; after two days of
  overtime, the longest COP on record, no deal is reached.
- Iran strikes US bases in Bahrain and two tankers in the Strait of
  Hormuz as a US blockade enters its 130th day; 25 tankers hit in a
  week, Brent crude at $92.57.
- Russian drones kill four near Kyiv and flatten a block in Dymer,
  where 14 are missing; 186 drones came overnight, 161 shot down.
- Briefs: Democrats clinch 258 House seats, the most since 1992;
  Liverpool thrash 10-man Man Utd 4-0 at Anfield; India post a
  record 720/9 in the Wellington Test; South Korea's education
  minister resigns over an AI cheating scandal; 3 dead and 50
  missing in an Indonesia factory fire; a Russian cargo ship burns
  off Finland; Verstappen wins the Las Vegas Grand Prix.
- A stats strip (37 stories, 9 regions, 25 tankers, 186 drones,
  258 seats, Brent $92.57), a markets strip (S&P 500 6,910.39
  -3.70%, Nasdaq 22,617.73 -5.28%, Dow 48,147.33 -1.93%, VIX 35.89,
  gold $3,515.40) and a world map marking 20 places.

## How it works

`main.py` is pure Python 3 standard library. It draws every pixel
itself — a hand-built vector serif font (strokes on a 9x16 grid,
with serif ticks on vertical stems), gradient skies, shaded
illustrations, a world map and a hand-written PNG encoder
(`zlib` + `struct`) — with no network, no clock and no randomness,
so two runs write byte-identical output.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

The image is written to `out/entry.png` (1024x1024, under 1 MiB).
