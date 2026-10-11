"""Turn on-screen script text into text a TTS engine reads naturally.

Rules follow the master prompt: "$1.14 trillion" -> "one point one four trillion dollars",
"£45 billion" -> "forty-five billion pounds", "5.31%" -> "five point three one percent".
"""
import re

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
ORD = {"one": "first", "two": "second", "three": "third", "five": "fifth", "eight": "eighth",
       "nine": "ninth", "twelve": "twelfth"}


def int_words(n: int) -> str:
    if n < 20:
        return ONES[n]
    if n < 100:
        t, o = divmod(n, 10)
        return TENS[t] + ("-" + ONES[o] if o else "")
    if n < 1000:
        h, r = divmod(n, 100)
        return ONES[h] + " hundred" + (" " + int_words(r) if r else "")
    for size, name in ((10**12, "trillion"), (10**9, "billion"), (10**6, "million"), (1000, "thousand")):
        if n >= size:
            q, r = divmod(n, size)
            return int_words(q) + " " + name + (" " + int_words(r) if r else "")
    raise ValueError(n)


def ordinal_words(n: int) -> str:
    w = int_words(n)
    head, _, last = w.rpartition("-") if "-" in w else ("", "", w)
    if last in ORD:
        last = ORD[last]
    elif last.endswith("y"):
        last = last[:-1] + "ieth"
    else:
        last += "th"
    return (head + "-" if head else "") + last


def num_words(s: str) -> str:
    """'1.14' -> 'one point one four', '56.7' -> 'fifty-six point seven', '36,000' -> 'thirty-six thousand'."""
    s = s.replace(",", "")
    if "." in s:
        a, b = s.split(".")
        return int_words(int(a)) + " point " + " ".join(ONES[int(d)] for d in b)
    return int_words(int(s))


def year_words(y: int) -> str:
    if 2000 <= y <= 2009:
        return "two thousand" + ("" if y == 2000 else " " + ONES[y - 2000])
    hi, lo = divmod(y, 100)
    return int_words(hi) + " " + (int_words(lo) if lo >= 10 else "oh " + ONES[lo] if lo else "hundred")


MONTHS = "January February March April May June July August September October November December".split()
NUM = r"\d[\d,]*(?:\.\d+)?"


def normalize(text: str) -> str:
    t = text
    t = t.replace("S&P", "S and P").replace("IMF", "I-M-F")
    t = t.replace("World War II", "World War Two")
    t = re.sub(r"\bAAA\b", "triple A", t)
    t = re.sub(r"(\d+)-year", lambda m: int_words(int(m.group(1))) + "-year", t)
    t = re.sub(r"mid-(\d{4})", lambda m: "mid " + year_words(int(m.group(1))), t)
    # "23 September 2022" -> "September twenty-third, twenty twenty-two"
    t = re.sub(r"\b(\d{1,2}) (%s) (\d{4})" % "|".join(MONTHS),
               lambda m: f"{m.group(2)} {ordinal_words(int(m.group(1)))}, {year_words(int(m.group(3)))}", t)
    t = re.sub(r"\$(%s) (trillion|billion|million)" % NUM, lambda m: f"{num_words(m.group(1))} {m.group(2)} dollars", t)
    t = re.sub(r"£(%s) (trillion|billion|million)" % NUM, lambda m: f"{num_words(m.group(1))} {m.group(2)} pounds", t)
    t = re.sub(r"\$(%s)" % NUM, lambda m: f"{num_words(m.group(1))} dollars", t)
    t = re.sub(r"(%s)%%" % NUM, lambda m: f"{num_words(m.group(1))} percent", t)
    t = re.sub(r"\b(1[89]\d\d|20\d\d)\b", lambda m: year_words(int(m.group(1))), t)
    t = re.sub(NUM, lambda m: num_words(m.group(0)), t)
    return t


if __name__ == "__main__":
    for s in ["In August 2026, America's debt crossed $40 trillion.", "$1.14 trillion", "£45 billion", "5.31%",
              "On 23 September 2022, the British", "more than $115,000 for", "since 2001.", "2007", "around $36,000",
              "about $73.", "S&P stripped America of its perfect AAA credit rating", "By mid-2026, 56.7%", "30-year",
              "according to the IMF", "World War II", "$5.5 billion", "1917", "2030"]:
        print(f"{s!r:60} -> {normalize(s)}")
