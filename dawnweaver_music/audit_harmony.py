"""Record every pitched note the recorded-instrument scores render and flag out-of-key notes.

Run: python audit_harmony.py
"""
import collections
import numpy as np
import sampler
from songs import chord

NAMES = "C C# D Eb E F F# G G# A Bb B".split()
log = []
_render = sampler.Instrument.render
_add = sampler.StereoMix.add
_last = {}


def render(self, midi=60, dur=None, vel=0.8, **kw):
    _last["note"] = (midi, dur) if self.pitched else None
    return _render(self, midi, dur, vel, **kw)


def add(self, bus, sig, beat, **kw):
    if _last.get("note"):
        midi, dur = _last["note"]
        log.append((bus, beat, int(round(midi)), (dur or 0) / self.spb))
    _last["note"] = None
    return _add(self, bus, sig, beat, **kw)


sampler.Instrument.render = render
sampler.StereoMix.add = add


def audit(name, run, prog, bpb, scale, extra_ok=lambda chordname, pc: False):
    log.clear()
    run()
    bad = collections.Counter()
    for bus, beat, m, dur in log:
        if bus in ("perc", "timp"):
            continue
        bar = int(beat // bpb) % len(prog)
        cn = prog[bar]
        pcs = {t % 12 for t in chord(cn, 4)[1]}
        pc = m % 12
        if pc not in scale and pc not in pcs and not extra_ok(cn, pc):
            bad[(bus, bar + 1, cn, NAMES[pc])] += 1
    print(f"{name}: {len(log)} notes, out-of-key: {sum(bad.values())}")
    for k, v in sorted(bad.items(), key=lambda x: x[0][1])[:20]:
        print("   ", k, v)


if __name__ == "__main__":
    import violin_real, orchestral_real as OR, ambient_real as AR
    for mod in (violin_real, OR, AR):
        mod.export = lambda *a, **k: None
        mod.write_midi = lambda *a, **k: None
    o = AR.extra(OR.Orchestra())
    G = {7, 9, 11, 0, 2, 4, 6}
    D = {2, 4, 6, 7, 9, 11, 1}
    Amin = {9, 11, 0, 2, 4, 5, 7}
    Cmin = {0, 2, 3, 5, 7, 8, 10}
    audit("violin", violin_real.main, violin_real.PROG, 4, Amin)
    audit("boss", lambda: OR.boss(o),
          ["Cm", "Cm", "Ab", "G", "Cm", "Ab", "Fm", "G", "Cm", "Db", "Bb", "G", "Ab", "Bb", "Gm", "Cm",
           "Fm", "Db", "Eb", "G", "Cm", "Bb", "Ab", "G", "Fm", "Ab", "G", "G", "Cm", "Db", "Cm", "G"], 4, Cmin)
    audit("victory", lambda: OR.victory(o), ["D", "Em", "D"], 4, D)
    audit("title", lambda: AR.title(o),
          ["D", "G", "D", "A", "D", "Bm", "G", "A", "D", "F#m", "G", "A", "Bm", "G", "D", "A", "G", "A", "Bm", "G",
           "G", "A7", "D", "D"], 3, D)
    audit("field", lambda: AR.field(o),
          ["G", "D", "Em", "C", "G", "D", "C", "D", "Em", "C", "G", "D", "Am", "C", "D", "D",
           "G", "D", "Em", "C", "Am", "D", "G", "D"], 4, G)
