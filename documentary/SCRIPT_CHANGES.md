# Script changes after the approved script

The brief asks that material changes to the script be clearly identified, not slipped in silently. This
file lists every line added after the approved script. These lines were added at the channel owner's
request ("add what happened to Rome and how it's related to the US in the intro, and how it affects the
common American, like higher import costs").

- **No approved sentence was removed or reworded.** `qa.py` checks the approved sentences word for word
  against the brief.
- Added lines carry `{n=new}` in `script.txt`. `qa.py` fails if any of them is missing from this file.
- The production sheet marks each line as "approved script" or "added".

Pace: the whole film now runs at **1.15×** (`!tempo 1.15` in `script.txt`). Narration is synthesised 15%
faster, and every gap, pause, card and animation is tightened by the same factor. This is a delivery change
only; no words changed.

## 1. Cold open: the Roman mirror

Inserted after "Just interest." and its beat, before "So is this the beginning of the end?". It gives
the big question a historical precedent, then draws the honest distinction.

| Line | Basis / evidence | Status |
|---|---|---|
| This has happened before. | Framing line | — |
| Nearly 1,800 years ago, the Roman Empire had its own money problem. | The Crisis of the Third Century (AD 235–284); the debasement peaked in the 260s, about 1,760 years ago | Standard history |
| To pay its soldiers and fund its wars, Rome quietly watered down its money. | Military pay rises (Septimius Severus, Caracalla) and constant wars drove repeated debasement of the silver coinage | Standard history |
| Over about two and a half centuries, its silver coins went from almost pure silver to only a few percent silver. | Denarius around 95% silver under Augustus (c. AD 14), about 50% under Septimius Severus (c. AD 200), around 5% or less in the antoninianus under Gallienus (260s); roughly 250 years. Numismatic estimates (K. Harl, *Coinage in the Roman Economy*, 1996; D. Walker, *The Metrology of the Roman Silver Coinage*, 1976–78) | Approximate; the chart says so. **Re-verify before publishing** |
| Prices soared, and trust in the money collapsed. | Steep price rises in the later 3rd century (papyrus price records from Roman Egypt), especially after Aurelian's coinage reform of 274 | Standard history |
| In the year 301, Emperor Diocletian tried to cap prices by decree. | Diocletian's Edict on Maximum Prices, AD 301 | Standard history |
| It didn't work. | Historians generally judge the edict ineffective: goods left the markets and it was soon disregarded | Standard history |
| The Western Empire held on for almost two more centuries, until the year 476. | Deposition of Romulus Augustulus, AD 476, the conventional date for the fall of the Western Empire (175 years after 301) | Standard history |
| It didn't collapse in a day. It weakened slowly, as its costs outran its income and its money lost the trust of its people. | Summary of the fiscal and monetary strain; consistent with Part 5's "slow chain reaction" | Interpretation, framed as such |
| America is not Rome. | Honest distinction, keeping the comparison measured | — |
| It borrows instead of debasing its coins, and its economy is the largest in the world. | The US finances deficits with Treasury securities; it has the largest nominal GDP (BEA; IMF WEO) | Fact |
| Different tools, same question: how long will the world keep trusting the money? | Bridges to the script's own theme of trust (Part 4, final line) | Framing |

## 2. What it means for ordinary Americans

| Where | Line | Basis / evidence | Status |
|---|---|---|---|
| Part 3, Door 1 (after the line on higher borrowing costs) | For families, this isn't abstract. | Framing | — |
| | Mortgage rates move with Treasury yields. | US 30-year mortgage rates track long-term Treasury yields (the 10-year yield plus a spread) | Well-established relationship |
| | On a 30-year mortgage of $400,000, every extra percentage point adds roughly $260 to the monthly payment. | Standard amortisation: $2,398/month at 6% vs $2,661/month at 7%, which is +$263/month (≈ $3,156/year). On screen with the inputs, labelled ILLUSTRATION | Exact arithmetic (`data.mortgage_payment`) |
| Part 3, Door 2 (after the foreign-investors question) | A weaker dollar also makes imports more expensive. | Exchange-rate pass-through: a weaker dollar raises import prices, partially and with a lag, because many imports are invoiced in dollars | Hedged ("can") |
| | Foreign sellers want more dollars for the same goods, so phones, cars, clothes and coffee can all cost more. | The same mechanism; product names are examples of heavily imported goods (no brands) | Hedged ("can") |
| | Your paycheck buys less, even if the number on it stays the same. | What inflation does to real wages | Definition |
| Part 3, Door 3 (after "payments could be delayed") | That could include Social Security checks, military pay and veterans' benefits. | Treasury and independent analysts warned in the 2011 and 2023 debt-limit standoffs that such payments could be delayed if the limit were breached | Hedged ("could") |
| Conclusion (after "But the direction is clear.") | For most Americans, the danger won't arrive as a headline about collapse. | Summary of the scenarios above | Framing |
| | It would show up quietly: in pricier loans, pricier imports, and less room in the budget for everything else. | Summary of door 1 (rates), door 2 (dollar) and Part 1 (interest crowding out other spending) | Conditional ("would") |
