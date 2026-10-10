"""Soft music bed for the SimpleMoney intro: warm pad, gentle pluck arpeggio, a pen tick on each board change."""
import sys, wave
import numpy as np

SR, DUR = 48000, 57.0
BPM = 84; BEAT = 60 / BPM
t = np.arange(int(SR * DUR)) / SR
out = np.zeros_like(t)
midi = lambda m: 440 * 2 ** ((m - 69) / 12)

# I - V - vi - IV in C, two bars each
chords = [[48, 55, 60, 64], [43, 55, 59, 62], [45, 52, 57, 60], [41, 53, 57, 60]]
bar = 4 * BEAT
rng = np.random.default_rng(7)

def env(n, a, r):
    e = np.ones(n); A, R = int(a * SR), int(r * SR)
    e[:A] = np.linspace(0, 1, A); e[-R:] *= np.linspace(1, 0, R); return e

i = 0; start = 0.0
while start < DUR:
    ch = chords[i % 4]; length = min(2 * bar, DUR - start)
    s, n = int(start * SR), int(length * SR)
    seg = np.arange(n) / SR
    pad = sum(np.sin(2*np.pi*midi(m)*(1+d)*seg + rng.random()*6) for m in ch for d in (-0.002, 0.002))
    out[s:s+n] += 0.05 * pad * env(n, 1.2, min(1.2, length/2))
    # pluck arpeggio in eighths, an octave up
    notes = [ch[1]+12, ch[2]+12, ch[3]+12, ch[2]+12]
    for k in range(int(length / (BEAT / 2))):
        ps = s + int(k * BEAT / 2 * SR); pn = int(1.2 * SR)
        if ps + pn > len(out): break
        pt = np.arange(pn) / SR; f = midi(notes[k % 4])
        out[ps:ps+pn] += 0.06 * (np.sin(2*np.pi*f*pt) + 0.25*np.sin(4*np.pi*f*pt)) * np.exp(-pt * 5)
    start += 2 * bar; i += 1

# soft pen tick at each board change
for bt in [5.2, 8.4, 13.2, 20.4, 25.6, 33.0, 40.0, 45.0]:
    s = int(bt * SR); n = int(0.05 * SR)
    noise = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 90)
    out[s:s+n] += 0.12 * np.convolve(noise, np.ones(6) / 6, 'same')

# fade in, long fade out under the end card
out *= np.clip(t / 0.6, 0, 1) * np.clip((DUR - t) / 4.0, 0, 1)
# light stereo: pad a touch wider by a tiny delay
d = int(0.012 * SR)
L, R = out, np.concatenate([np.zeros(d), out[:-d]])
st = np.stack([L, R], 1); st /= np.abs(st).max() * 1.12
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype('<i2').tobytes())
