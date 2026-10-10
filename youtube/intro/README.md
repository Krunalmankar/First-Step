# SimpleMoney channel intro

A 57-second channel trailer built from the SimpleMoney design system: ledger paper, pen blue, one marker swipe, word-by-word captions and the end card.

- `simplemoney-intro.mp4`: 1920×1080, 59.94 fps, H.264, AAC 48 kHz, with the music bed only (no voice yet).
- `music-bed.wav`: the music on its own (−16 LUFS), so you can duck it under your voice.
- `intro.html`: the animation. Open it in a browser to watch it loop in real time.
- `render.mjs`, `music.py`: re-render after edits: `python3 music.py raw.wav`, then `node render.mjs simplemoney-intro.mp4 music-bed.wav`.

## Voice-over script

Record from this sheet and keep each line inside its window. If a line runs long, move that scene's times in `SCENES` in `intro.html` and re-render.

| # | Time | Board | Voice-over | On screen |
|---|---|---|---|---|
| 1 | 0:00–0:05 | Hook (night) | "Money. Everyone has an opinion on it. Very few make it simple." | Ghost word "Money", coin stacks rising · Save / Invest / Plan taxes |
| 2 | 0:05–0:08 | Disclaimer | "Quick note: this channel is education, not advice." | This is education, not advice. |
| 3 | 0:08–0:13 | Caption | "Money feels complicated. Let's keep it simple." | Money feels **complicated** (loss) · Let's keep it **simple** (pen) |
| 4 | 0:13–0:20 | Agenda | "Here you'll learn savings and FDs, SIPs and mutual funds, tax made clear, and the catch, every time." | 1–4, the 4th in loss |
| 5 | 0:20–0:26 | Stat tiles | "For example: ten thousand rupees a month, for twenty years, at an assumed twelve percent a year…" | ₹10,000 · 20 yrs · 12% · RETURN ASSUMED |
| 6 | 0:26–0:33 | Growth chart | "…becomes about one crore. You only put in twenty-four lakh. At seven percent, about fifty-two lakh." | Lines draw, count-up to ≈ ₹1 crore, marker swipe |
| 7 | 0:33–0:40 | Two formats | "Two kinds of videos: Money Briefs when something changes, and Explainers when you want to know how it works." | Money Brief · Explainer |
| 8 | 0:40–0:45 | Promise | "No tips. Just the maths." | No tips. Just the **maths.** |
| 9 | 0:45–0:57 | End card | "This is SimpleMoney. Subscribe, and let's make money simple." | SimpleMoney · Like / Share / Subscribe |

## Numbers check

₹10,000 a month for 20 years (240 instalments, monthly compounding, start of month):

| Scenario | Value at year 20 | On screen |
|---|---|---|
| Put in | ₹24.0 lakh | PUT IN · ₹24 L |
| 7% a year | ₹52.4 lakh | AT 7% · ₹52 L |
| 12% a year (assumed) | ₹99.9 lakh | ≈ ₹1 crore, ASSUMED 12% P.A. |

## Mixing your voice

Put the voice on top and duck `music-bed.wav` about 12–15 dB under it. Mix to about −14 LUFS integrated with peaks under −1 dBTP. The end card holds from 0:45 to 0:57 so there is room for YouTube end-screen elements.
