"""Harmony helpers that keep added voices inside the current chord."""
from songs import chord


def harmony_under(notes, prog, beats_per_bar=4, min_gap=3, max_gap=9):
    """For each (beat, dur, midi) melody note, pick the highest tone of the chord sounding at
    that beat that lies at least `min_gap` semitones below the melody (a 3rd/4th/6th under)."""
    out = []
    for b, d, m in notes:
        name = prog[min(len(prog) - 1, int(b // beats_per_bar))]
        pcs = {t % 12 for t in chord(name, 4)[1]}
        cand = [p for p in range(m - max_gap, m - min_gap + 1) if p % 12 in pcs]
        if cand:
            out.append((b, d, max(cand)))
    return out
