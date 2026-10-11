"""End-to-end build: narration -> timeline -> score/mix -> frames -> final MP4 + SRT + production sheet.

    python3 build.py [--backend kokoro|edge] [--skip-tts] [--skip-video] [--reuse-video] [--skip-audio]
"""
import argparse
import csv
import re
import shutil
import subprocess
from pathlib import Path


HERE = Path(__file__).parent
OUT = HERE / "output"
TITLE = "Could the United States Collapse Because of Its Debt"

VOICE_DIRECTION = {
    0: "Low, controlled, intriguing; hold silence after the opening line; slower on the military/Medicare comparison",
    1: "Calm and conversational, tightening from 'But here's where it turns dangerous'; beat of emphasis on key figures",
    2: "Measured and credible on dates and agencies; slow and heavy on 'not one of the three'; unhurried on 5.31%",
    3: "Serious and analytical; faster in the UK story; quiet and creeping for the dollar; puzzled then grave on default",
    4: "Confident, cautiously reassuring through the four advantages; sharp turn to quiet seriousness on 'Not quite.'",
    5: "Reflective, slow, almost elegiac; a small lift of hope on 'Is that guaranteed? No.'",
    6: "Reflective, clear, decisive; stress 'unlikely', 'possible', 'worth watching'; land the final line slowly",
    7: "Warm, direct, conversational; a hint of intrigue on 'even scarier'",
}

SCENES = {
    "title40": ("'$40' counts up over black, 'TRILLION' in accent; production note fades in", "Low impact hit; tense pad + 56 bpm pulse; near-silence on the pause"),
    "owes": ("Live-style debt counter from $40.31T (Debt to the Penny, 8 Oct 2026); 'and still climbing'", "Tension pad and pulse continue"),
    "milestones": ("Timeline $38T Oct 2025 -> $39T Mar 2026 -> $40T Aug 2026; five-month bracket", "Pulse lifts slightly"),
    "outlays": ("Ranked bar chart of FY2026 outlays; interest bar (accent) grows first, then defense, Medicare, Social Security", "Soft tick as each bar enters"),
    "interest_counter": ("Interest counter at ~$36,245/s labelled FY2026 average; ROADS / SCHOOLS struck through, INTEREST in accent", "Music drops to near-silence on the pause"),
    "question": ("Typographic question, word by word; 'Stay with me.'", "Pulse stops; pad only"),
    "_title": ("Title card: SIMPLEMONEY, documentary title, production note", "Riser into a soft hit; Part 1 pad begins"),
    "_chapter": ("Minimal chapter card (part number in accent, title)", "Riser and soft low hit"),
    "spend_list": ("Six cards appear as each spending category is named; 'Interest on the debt' outlined in accent", "Minimal ambient pad, light pulse"),
    "spend_vs": ("Bars: spent $7.4T vs collected $5.4T; hatched accent gap ≈ $2.0T", "Pad, light pulse"),
    "hundred": ("100-square grid fills to 73 blue squares; '$100 spent / only $73 collected'", "Pad, light pulse"),
    "deficit": ("Counter to $1,993 billion; '≈ $5.5 billion every single day'", "Pad, light pulse"),
    "bonds": ("Diagram: US Treasury <-> investors (bonds one way, cash the other) over an engraved rosette texture", "Soft ticks join"),
    "machine": ("Looping cause-and-effect diagram lights step by step; '+$115B'; refinancing node feeds the loop", "Rhythm builds"),
    "one_in_five": ("Five dollar tiles, one lifts away in accent '→ interest'; ≈21% calculation shown", "Rhythm continues"),
    "per_person": ("Counter to $115,000+ 'for every man, woman and child'", "Rhythm continues"),
    "spin": ("The loop with orbiting markers that accelerate", "Fastest tempo of Part 1 into the chapter card"),
    "nobody": ("Quoted thought revealed word by word; 'Except… they already have.' in accent", "Darker pad, low pulse"),
    "downgrades": ("Timeline of the three downgrades with old -> new ratings (agency names as text, no logos)", "Low hit on each downgrade"),
    "none_perfect": ("Three panels: AA+, AA+, Aa1; 'Not one perfect score.'", "Near-silence before the line"),
    "yield": ("30-year yield chart 2007–2025 (annual avg) to 5.31% Aug 2026 close; dashed line back to 2007; 5.22% auction callout", "Dark pad, slow pulse"),
    "charging": ("Typographic pairs: still lending / charging more; not collapse / nervous", "Pad only"),
    "doors": ("Three doors appear; tag 'SCENARIOS, NOT PREDICTIONS'", "Measured low pulses"),
    "door1": ("Door 1 swings open; sub-chapter title", "Whoosh"),
    "door1_quote": ("Hypothetical investor quote, labelled SCENARIO", "Low pulses"),
    "door1_chain": ("See-saw: bond prices down / yields up; five 'costs more' cards", "Low pulses"),
    "door1_cbo": ("Bars: net interest $1.14T (FY2026 actual) vs $2.1T (2036, CBO projection, hatched)", "Low pulses"),
    "uk_intro": ("'Far-fetched?' -> UNITED KINGDOM 2022", "Tempo rises"),
    "uk": ("Timeline 23 Sep (mini-budget £45bn) -> 28 Sep (BoE up to £65bn) -> 20 Oct (PM resigns) with schematic gilt-yield spike; pound record-low callout", "Most propulsive music: 108 bpm pulse and ticks; hit on the resignation"),
    "uk_imagine": ("'That was Britain.' -> 'Now imagine…'", "Music thins after the pause"),
    "door2": ("Door 2 opens; sub-chapter title", "Whoosh; thin, unsettling high ambience"),
    "door2_print": ("A $1 note shrinks and fades; Prices ↑ / Savings ↓; investors' question", "Thin ambience"),
    "door2_creep": ("A slow line erodes downward: 'No crash. It creeps in.'", "Thin ambience"),
    "door2_reserve": ("Line chart: dollar share of FX reserves 71% (2000) -> 56.7% (Q2 2026)", "Thin ambience"),
    "door3": ("Door 3 opens; sub-chapter title", "Whoosh; low pulses return"),
    "door3_strange": ("'Has the money ≠ Fails to pay' -> 'How?' -> POLITICS", "Low pulses"),
    "door3_limit": ("Debt-limit gauge: $40.31T owed vs $41.1T limit; '2027 (estimated)' tagged ESTIMATE", "Low pulses"),
    "door3_panic": ("Row of payments, one 'Delayed'; 'Not because America is broke. Because it chose to stumble.'", "Low pulses; dip on the pause"),
    "crisis_collapse": ("CRISIS ≠ COLLAPSE; CBO warning panel", "Pad only"),
    "cards": ("Four face-down cards: 'Why is America still standing?'", "Cautious optimism: major-key pad, 92 bpm"),
    "adv1": ("Card 1 flips; stacked bar of reserve shares USD 56.7%, EUR 20.6%, others 22.7%", "Controlled momentum"),
    "adv2": ("Card 2: '$30T+ economy' and '+$169B revenue'", "Controlled momentum"),
    "adv3": ("Card 3: borrows in $ -> repays in $; 'No foreign-currency trap'", "Controlled momentum"),
    "adv4": ("Card 4: banks, governments, funds -> US Treasuries; 'every auction has found buyers'", "Controlled momentum"),
    "safe": ("'So America is safe, right?' -> hold -> 'Not quite.' in accent", "Abrupt musical cut on 'Not quite.' with a low hit"),
    "trust": ("Cards connect into the word TRUST, which cracks and falls apart on 'all at once'", "Low drone only; crack SFX"),
    "rome": ("Original line drawing of a colonnade with a fallen and a broken column; slow push-in", "Reflective pad and sparse piano"),
    "chain_intro": ("'Not barbarians at the gates.' -> 'A slow chain reaction.'", "Reflective"),
    "chain": ("Five-step chain lights in sync, tagged 'A POSSIBLE PATH — NOT A PREDICTION'; deficit inset $2.0T -> $3.1T (2036, CBO)", "Slow pulse under piano"),
    "record2030": ("'2030' then debt-to-GDP chart crossing the 1946 record (106%), projection dashed and tagged", "Soft hit on 2030"),
    "slipping": ("Final chain step lights, then the whole chain fades slowly", "Sparse piano"),
    "window": ("A window of light slowly narrows; 'Guaranteed? No.' and the three remedies", "Small lift of hope: major-key pad"),
    "conc_q": ("The central question, word by word", "Pad"),
    "futures": ("Three futures rated UNLIKELY / POSSIBLE / WORTH WATCHING", "Gradual controlled build"),
    "conc_cbo": ("Bars: debt held by the public 101% (2026) -> 120% (2036, CBO projection); interest $1.14T -> $2.1T", "Build continues"),
    "final": ("The final two lines, the second held", "Clean resolve on a D-major chord"),
    "outro": ("Call to action; two 'Next?' topic cards", "Light and warm"),
    "_end": ("End card: SIMPLEMONEY, sources note, synthetic-voice disclosure", "Warm pad fades out"),
}


def run(cmd):
    print("$", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def fmt_ts(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"


def chunks(text, maxc=84):
    """Split a sentence into subtitle cues of at most ~2 lines x 42 chars at natural breaks."""
    if len(text) <= maxc:
        return [text]
    parts = re.split(r"(?<=[,;:?!.…])\s+", text)
    out, cur = [], ""
    for p in parts:
        if len(cur) + len(p) + 1 <= maxc:
            cur = (cur + " " + p).strip()
        else:
            if cur:
                out.append(cur)
            while len(p) > maxc:
                cut = p.rfind(" ", 0, maxc)
                out.append(p[:cut])
                p = p[cut + 1:]
            cur = p
    if cur:
        out.append(cur)
    return out


def two_lines(s, maxl=42):
    """Break a cue into two balanced lines, never between a figure and its unit ("$40 | trillion")."""
    if len(s) <= maxl:
        return s
    best, best_cost = None, 1e9
    for i, ch in enumerate(s):
        if ch != " ":
            continue
        a, b = s[:i], s[i + 1:]
        cost = abs(len(a) - len(b)) + 40 * (max(len(a), len(b)) > maxl + 4)
        prev, nxt = a.split()[-1], b.split()[0]
        if re.match(r"^[$£]?\d", prev) and re.match(r"^(trillion|billion|million|percent|pounds|dollars)", nxt):
            cost += 100
        if prev.lower() in ("a", "an", "the", "of", "to", "in", "on", "by", "for", "and", "or", "at", "up"):
            cost += 8
        if prev[:1].isupper() and nxt[:1].isupper() and not prev.endswith((",", ".")):
            cost += 14   # keep names together: "United States", "Bank of England", "Social Security"
        if prev.endswith((",", ".", ":", ";", "?")):
            cost -= 6
        if cost < best_cost:
            best, best_cost = i, cost
    return s[:best] + "\n" + s[best + 1:]


def write_srt(tl, path):
    n, lines = 1, []
    for u in tl["units"]:
        parts = chunks(u["text"])
        total = sum(len(p) for p in parts)
        t = u["start"]
        for p in parts:
            d = (u["end"] - u["start"]) * len(p) / total
            lines.append(f"{n}\n{fmt_ts(t)} --> {fmt_ts(t + d)}\n{two_lines(p)}\n")
            n += 1
            t += d
    path.write_text("\n".join(lines))


def write_sheet(tl, path):
    seg_of = {}
    for s in tl["segments"]:
        for i in s["units"]:
            seg_of[i] = s
    chap = {c["num"]: c["title"] for c in tl["chapters"]}
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["chapter_no", "chapter_title", "sentence_no", "start", "end", "duration_s", "narration_exact",
                    "spoken_as", "script_change", "voice_direction", "emotion_preset", "emphasis", "speed", "scene_id",
                    "visual_description", "asset_source_rights", "music_sfx_cue", "transition_out"])
        units = tl["units"]
        for k, u in enumerate(units):
            s = seg_of[u["idx"]]
            vis, mus = SCENES.get(u["scene"], ("", ""))
            nxt = units[k + 1]["scene"] if k + 1 < len(units) else "_end"
            trans = "hold (same scene)" if nxt == u["scene"] else "dissolve through background (0.3 s)"
            if k + 1 < len(units) and units[k + 1]["chapter"] != u["chapter"]:
                trans = "dissolve to chapter card"
            w.writerow([u["chapter"], chap[u["chapter"]], u["idx"] + 1, fmt_ts(u["start"]), fmt_ts(u["end"]),
                        round(u["end"] - u["start"], 2), u["text"], u["spoken"],
                        "added (see SCRIPT_CHANGES.md)" if u.get("new") else "approved script",
                        ("Sub-chapter title, narrated and shown on screen. " if u["kind"] == "title" else "")
                        + VOICE_DIRECTION[u["chapter"]], u.get("emotion", ""),
                        "; ".join(re.findall(r"\*\*?([^*]+)\*\*?", u.get("marked", ""))) +
                        (" (rising question)" if u.get("rise") else ""), u["speed"], u["scene"], vis,
                        "Original procedural motion graphic created for this project (code in this repo); "
                        "font: Inter (SIL Open Font License 1.1)", mus, trans])


def write_description(tl, path):
    """YouTube description: hook, production note, chapter timestamps, sources, disclosures."""
    starts = {}
    for s in tl["segments"]:
        if s["name"] == "_chapter":
            starts.setdefault(s["chapter"], s["start"])
    first_outro = next(u for u in tl["units"] if u["chapter"] == 7)
    starts[0], starts[7] = 0.0, first_outro["start"] - 0.5
    names = {0: "Cold open: $40 trillion, and a lesson from Rome", 1: "The machine that never stops borrowing",
             2: "The warning signs are already here", 3: "Three ways this could go terribly wrong",
             4: "So why hasn't it happened yet?", 5: "Could America fall like Rome?", 6: "Conclusion: three futures",
             7: "Your turn"}

    def mmss(t):
        return f"{int(t // 60)}:{int(t % 60):02d}"

    src = (HERE / "SOURCES.md").read_text()
    links = src[src.find("## Description-ready source list"):src.find("## Claim-by-claim register")]
    links = "\n".join(ln.replace("*", "") for ln in links.splitlines()[1:] if ln.strip())
    text = f"""{TITLE}?

America owes more than $40 trillion, and in fiscal year 2026 it spent $1.14 trillion on interest alone: more than its entire military, more than Medicare. Rome once faced its own money problem and quietly watered down its silver coins. Is America heading the same way, or is this one of the most overhyped fears in finance? We look at the evidence: three credit downgrades, the highest 30-year yields since 2007, the UK's 2022 gilt crisis, the dollar's shrinking share of world reserves and the debt limit. We also show what each scenario would mean for ordinary Americans: mortgage payments, the price of imports, and the paycheck that buys less.

Figures verified as of 11 October 2026. Fiscal year 2026 ran from 1 October 2025 to 30 September 2026. The three "doors" and the chain reaction are scenarios, not predictions; projections are labelled on screen.

CHAPTERS
""" + "\n".join(f"{mmss(starts[k])} {names[k]}" for k in sorted(starts)) + f"""

SOURCES
{links}

PRODUCTION NOTES
Narration uses a synthetic (AI-generated) voice. All graphics, music and sound design are original; the video contains no archival or news footage. Every chart shows its source and period on screen.
This video is for education and is not financial advice.
"""
    path.write_text(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="kokoro", choices=["kokoro", "edge"])
    ap.add_argument("--skip-tts", action="store_true")
    ap.add_argument("--flat", action="store_true", help="narration without expressive shaping (A/B)")
    ap.add_argument("--skip-video", action="store_true")
    ap.add_argument("--reuse-video", action="store_true", help="re-mux with the existing build/video_only.mp4")
    ap.add_argument("--skip-audio", action="store_true", help="reuse build/mix_final.wav and the voiceover stem")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    if not a.skip_tts:
        import tts
        tts.run(a.backend, a.flat)
    import timeline
    tl = timeline.build(a.backend)
    print("timeline:", tl["duration"], "s")

    if not (a.skip_audio and (HERE / "build" / "mix_final.wav").exists()):
        import audio
        audio.write_all(tl)   # mix, master to -14 LUFS, voiceover stem (timed to picture) at -16 LUFS

    write_srt(tl, OUT / f"{TITLE}.en.srt")
    write_sheet(tl, OUT / "production_sheet.csv")
    write_description(tl, OUT / "youtube_description.txt")
    shutil.copy(HERE / "build" / "timeline.json", OUT / "timeline.json")

    run(["ffmpeg", "-loglevel", "error", "-y", "-i", HERE / "build" / "voiceover.wav", "-b:a", "192k",
         OUT / "voiceover_narration.mp3"])
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", HERE / "build" / "music_sfx_stem.wav", "-b:a", "192k",
         OUT / "music_sfx_stem.mp3"])

    if not a.skip_video:
        import render
        video = HERE / "build" / "video_only.mp4"
        if not (a.reuse_video and video.exists()):
            shutil.rmtree(render.SEGDIR, ignore_errors=True)
            video = render.render_all()
            render.export_graphics()
        run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-i", HERE / "build" / "mix_final.wav",
             "-i", OUT / f"{TITLE}.en.srt", "-map", "0:v", "-map", "1:a", "-map", "2:s", "-c:v", "copy",
             "-c:a", "aac", "-b:a", "256k", "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
             "-metadata", f"title={TITLE}?", "-movflags", "+faststart", "-t", f"{tl['duration']:.3f}",
             OUT / f"{TITLE}.mp4"])
    print("done ->", OUT)


if __name__ == "__main__":
    main()
