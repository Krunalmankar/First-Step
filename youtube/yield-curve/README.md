# The Yield Curve, in the SimpleMoney look

Your Yield Curve video (V3, Oct 9, 2026) rebuilt in the SimpleMoney Explainer format: ledger paper, pen blue, one marker swipe per board, word-by-word captions, the chapter header and the 6-tab chapter nav. The narration is your existing voice track, unchanged.

- Length 12:02 (4 s disclaimer card + 11:48 narration + 10 s end card), 1920×1080, 59.94 fps, H.264 + AAC 320k.
- `yield-curve.html`: the whole video as one animated page. Open it in a browser to watch it loop (silent).
- `data.js`: the chart series, traced from the charts in the original video (Fed H.15, BLS, BEA via FRED, as of Oct 8, 2026).
- `render.mjs`, `build.sh`: re-render. `./build.sh <original-video.mp4> <out.mp4>` renders 4 chunks in parallel, joins them, delays the narration 4 s for the disclaimer and adds a quiet music tail under the end card (uses `../intro/music-bed.wav`).

The MP4 is not committed (GitHub's 100 MB file limit); re-render it with `build.sh`.

## Structure

The original's 14 chapters sit under the 6 nav tabs. The header shows the chapter as "Point 0X / 14".

| Nav tab | Chapters | Voice time |
|---|---|---|
| (cold open) | 2000 · 2006 · 2019, the title, the full 1977–2026 chart, five warning lights | 0:00–1:04 |
| Basics | 01 What is a yield curve | 1:04–1:40 |
| Inversion | 02 The flip · 03 Why it inverts · 04 Expectations | 1:40–3:18 |
| History | 05 The track record · 06 The big mistake | 3:18–5:32 |
| The twist | 07 The twist · 08 Un-inversion | 5:32–6:38 |
| Today | 09 October 2026 · 10 The 2026 dashboard · 11 Putting it together | 6:38–9:20 |
| What's next | 12 The 2027 scenario · 13 Five red alerts · 14 Is 2027 the year? · verdict | 9:20–11:48 |

Section cards (one word + a mono definition) open chapters 01, 03, 05, 06, 07, 10 and 11, at the same moments the original showed its chapter titles.

## Check before upload

- [ ] **Captions.** Each beat's kinetic caption was written from the on-screen text of the original, and each one appears when its beat starts. Watch once with sound and fix any caption that doesn't match the words being spoken (edit the `cap:` lists in `yield-curve.html`).
- [ ] **Chapter timestamps.** Every chapter now starts 4 s later than in your existing `youtube_description.txt`. Add 4 s to each timestamp, and add "0:00 Disclaimer".
- [ ] **Subtitles.** Shift `subtitles_en.srt` by +4 s (YouTube Studio can't offset it, but most subtitle editors can).
- [ ] **Disclaimer.** The card is on screen for the first 4 s, but the voice doesn't say it. The brand book asks for it to be said once.
- [ ] The 2027 domino chain is tagged "Hypothetical · not a forecast"; the example in chapter 08 is tagged "Example".
- [ ] End card holds 10 s for YouTube end-screen elements.
