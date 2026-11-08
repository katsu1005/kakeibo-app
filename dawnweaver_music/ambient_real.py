"""Title theme and field music with recorded instruments (VSCO 2 CE, CC0).

Run:  python ambient_real.py [title] [field]
"""
import os
import sys
import numpy as np
from synth import SR, midi_of, parse_line, write_midi
from sampler import Instrument, StereoMix, place_swell
from songs import OUT, chord, export
from songs2 import root_in
from orchestral_real import Orchestra, fit, mixdown
from harmony import harmony_under

rng = np.random.default_rng(31)
H = 0.008


def extra(o):
    I = Instrument
    o.ob = I("Woodwinds/Oboe/Vib")
    o.bn = I("Woodwinds/Bassoon/sus")
    o.cl = I("Woodwinds/Clarinet/susLong")
    o.fl_nv = I("Woodwinds/Flute/susNV")
    o.vs_pizz = I("Strings/Violin Section/Pizz")
    o.va_pizz = I("Strings/Viola Section/pizz")
    o.vc_pizz = I("Strings/Cello Section/pizzT")
    o.cb_pizz = I("Strings/Solo Contrabass/Pizz", force_fix=12)  # detector fails on short low plucks
    o.tri = I("Percussion", pattern=r"^Triangle3-Hit_v", pitched=False)
    o.tamb_shake = I("Percussion", pattern=r"^Tamb1-Shake", pitched=False)
    o.cym_swell = I("Percussion", pattern=r"^susCymb1-cresc-Long", pitched=False)
    return o


def legato(mx, bus, inst, notes, spb, vel, pan, release=0.3, overlap=0.06, vel_fn=None):
    for b, d, m in notes:
        v = vel * (vel_fn(b) if vel_fn else 1.0) * rng.uniform(0.95, 1.03)
        mx.add(bus, inst.render(fit(inst, m), d * spb + overlap, v, release=release), b, pan=pan,
               humanize=H * 0.5, rng=rng)


# =====================================================================
# Title  "暁を織る者"  D major, 3/4, 84 BPM, 24 bars (~51 s loop)
# =====================================================================
def title(o):
    bpm, nbars, bpb = 84, 24, 3
    spb = 60 / bpm
    loop_s = nbars * bpb * spb
    mx = StereoMix(loop_s + 7.0, bpm)
    prog = ["D", "G", "D", "A",
            "D", "Bm", "G", "A", "D", "F#m", "G", "A",
            "Bm", "G", "D", "A", "G", "A", "Bm", "G",
            "G", "A7", "D", "D"]
    mel = parse_line(" ".join([
        "A5:2 F#5:1", "D6:1.5 C#6:.5 B5:1", "G5:1 A5:1 B5:1", "A5:3",
        "A5:2 F#5:1", "C#6:1.5 B5:.5 A5:1", "B5:1 G5:1 E5:1", "C#5:1 E5:1 A5:1",
        "B5:2 D6:1", "D6:1.5 E6:.5 D6:1", "A5:1 F#5:1 D6:1", "C#6:3",
        "B5:1.5 C#6:.5 D6:1", "E6:2 C#6:1", "D6:1.5 C#6:.5 B5:1", "B5:2 A5:1",
        "G5:1.5 F#5:.5 E5:1", "E5:1 F#5:1 G5:1", "F#5:3"]), 4 * bpb)
    A = [e for e in mel if e[0] < 12 * bpb]
    A2 = [e for e in mel if 12 * bpb <= e[0] < 20 * bpb]
    coda = [e for e in mel if e[0] >= 20 * bpb]
    # intro motif on flute (bars 3-4) – foreshadows the theme
    motif = parse_line("A5:1 D6:1 E6:1 F#6:3", 2 * bpb)

    def dyn(b):
        bar = b / bpb
        if bar < 12:
            return 0.75
        if bar < 20:
            return 0.8 + 0.025 * (bar - 12)
        return 0.6

    legato(mx, "wind", o.fl, motif, spb, 0.6, 0.25)
    # A: solo horn sings the theme, an octave down
    legato(mx, "melody", o.hn_sus, [(b, d, m - 12) for b, d, m in A], spb, 0.8, -0.15, vel_fn=dyn)
    # A': violins take it, cellos an octave lower, flute joins on the last 4 bars
    legato(mx, "melody", o.vs_sus, A2, spb, 0.85, -0.35, vel_fn=dyn)
    legato(mx, "melody", o.vc_sus, [(b, d, m - 12) for b, d, m in A2], spb, 0.55, 0.35, vel_fn=dyn)
    legato(mx, "wind", o.fl, [(b, d, m) for b, d, m in A2 if b >= 16 * bpb], spb, 0.55, 0.25)
    # coda: oboe, gentle
    legato(mx, "wind", o.ob, coda, spb, 0.6, 0.2)

    harp_ev, pad_ev, bass_ev = [], [], []
    for bi, c in enumerate(prog):
        b0 = bi * bpb
        r4, t4 = chord(c[:2] if c.endswith("7") else c, 4)
        t4 = t4[:3]
        r2 = root_in(c.rstrip("7"), "D2")
        # harp: rising 8th-note arpeggio – the "weaving" figure
        pattern = [r4 - 12, t4[1] - 12, t4[2] - 12, r4, t4[1], t4[2]]
        for k, m in enumerate(pattern):
            v = 0.55 if k == 0 else 0.42
            mx.add("harp", o.harp.render(m, None, v * (0.85 if bi >= 20 else 1.0)), b0 + k * 0.5, pan=0.45,
                   humanize=H * 0.5, rng=rng)
            harp_ev.append((b0 + k * 0.5, 0.5, m))
        # strings bed
        dd = bpb * spb
        pv = 0.32 if bi < 4 or bi >= 20 else (0.38 if bi < 12 else 0.48)
        mx.add("pad", o.va_sus.render(fit(o.va_sus, t4[1] - 12), dd, pv, release=0.6), b0, pan=0.15, rng=rng)
        mx.add("pad", o.vc_sus.render(fit(o.vc_sus, r2 + 12), dd, pv + 0.05, release=0.6), b0, pan=0.3, rng=rng)
        if 4 <= bi < 20:
            mx.add("pad", o.vs_sus.render(fit(o.vs_sus, t4[2]), dd, pv * 0.8, release=0.6), b0, pan=-0.3, rng=rng)
        if bi >= 4:
            mx.add("low", o.cb_sus.render(fit(o.cb_sus, r2), dd, 0.45 if bi < 12 else 0.55, release=0.6), b0,
                   pan=0.35, rng=rng)
        if 12 <= bi < 20:  # horns hold harmony under the violins
            for m in t4[:2]:
                mx.add("pad", o.hn_sus.render(fit(o.hn_sus, m - 12), dd, 0.4, release=0.6), b0, pan=-0.15, rng=rng)
        for m in t4:
            pad_ev.append((b0, bpb, m))
        bass_ev.append((b0, bpb, r2))
        # glockenspiel sparkle on phrase starts
        if bi % 4 == 0:
            mx.add("glock", o.glock.render(fit(o.glock, r4 + 24), None, 0.35), b0, pan=0.25)

    # build into A' and the climax
    for bar in (12, 16):
        r = root_in(prog[bar - 1].rstrip("7"), "F2")
        mx.add("timp", o.timp_roll.render(r, 2 * spb, 0.55, release=0.05, fade_in=0.6), bar * bpb - 2, pan=-0.2)
        mx.add("timp", o.timp.render(root_in(prog[bar], "F2"), 1.5, 0.7, release=0.5), bar * bpb, pan=-0.2)
    place_swell(mx, "perc", o.cym_swell.render(vel=0.35), 16 * bpb)
    mx.add("perc", o.crash.render(vel=0.45), 16 * bpb, pan=0.4)

    gains = {"melody": 1.0, "wind": 0.85, "harp": 0.75, "pad": 0.6, "low": 0.5, "glock": 0.5,
             "timp": 0.6, "perc": 0.5}
    wet = {"melody": 0.38, "wind": 0.4, "harp": 0.4, "pad": 0.45, "low": 0.3, "glock": 0.5,
           "timp": 0.35, "perc": 0.4}
    loop_n = int(round(loop_s * SR))
    x = mixdown(mx, gains, wet, loop_n=loop_n, ir_decay=0.9, drive=1.0)
    export("dawnweaver_title_theme_real_loop", x, loop_n, "暁を織る者 (Title Theme)")
    write_midi(os.path.join(OUT, "dawnweaver_title_theme_real.mid"), bpm,
               [("Melody", 60, 0, motif + mel), ("Harp", 46, 1, harp_ev), ("Strings", 48, 2, pad_ev),
                ("Bass", 43, 3, bass_ev)], numerator=3)


# =====================================================================
# Field  "灯の谷を渡る風"  G major, 4/4, 108 BPM, 24 bars (~53 s loop)
# =====================================================================
def field(o):
    bpm, nbars = 108, 24
    spb = 60 / bpm
    loop_s = nbars * 4 * spb
    mx = StereoMix(loop_s + 6.0, bpm)
    prog = ["G", "D", "Em", "C", "G", "D", "C", "D",
            "Em", "C", "G", "D", "Am", "C", "D", "D",
            "G", "D", "Em", "C", "Am", "D", "G", "D"]
    A = parse_line(" ".join([
        "D5:1 G5:.5 A5:.5 B5:1 G5:1", "A5:1.5 G5:.5 F#5:1 D5:1", "E5:.5 F#5:.5 G5:1 B5:1 E6:1",
        "D6:1.5 C6:.5 B5:1 G5:1", "B5:1 D6:.5 B5:.5 A5:1 G5:1", "F#5:.5 G5:.5 A5:1 D5:2",
        "E5:1 G5:.5 E5:.5 C6:1 B5:.5 A5:.5", "A5:3 r:1"]))
    B = parse_line(" ".join([
        "B4:1 E5:1 G5:1.5 F#5:.5", "E5:1 C5:1 G4:2", "D5:1 G5:1 B5:1.5 A5:.5", "A5:2 F#5:1 D5:1",
        "C5:1 E5:1 A5:1.5 G5:.5", "G5:1 E5:1 C6:1.5 B5:.5", "A5:1 F#5:.5 G5:.5 A5:1 C6:1",
        "B5:.5 A5:.5 F#5:1 D5:2"]), 32)
    A2 = parse_line(" ".join([
        "D5:1 G5:.5 A5:.5 B5:1 D6:1", "F#6:1.5 E6:.5 D6:1 A5:1", "B5:.5 C6:.5 D6:1 G6:1 E6:1",
        "E6:1.5 D6:.5 C6:1 G5:1", "A5:1 C6:1 E6:1 D6:.5 C6:.5", "B5:1 A5:1 F#5:1 A5:1",
        "G5:3 B5:.5 A5:.5", "A5:2 F#5:1 D5:1"]), 64)

    # A: flute, B: oboe (with clarinet a 3rd/6th below), A': violins + flute an octave up
    legato(mx, "melody", o.fl, A, spb, 0.75, 0.15, overlap=0.04)
    legato(mx, "melody", o.ob, B, spb, 0.75, 0.1, overlap=0.04)
    under = harmony_under([e for e in B if e[1] >= 1], prog)
    legato(mx, "wind2", o.cl, under, spb, 0.45, -0.25, overlap=0.04)
    legato(mx, "melody", o.vs_sus, A2, spb, 0.8, -0.3, overlap=0.05)
    legato(mx, "wind2", o.fl, [(b, d, m + 12) for b, d, m in A2 if d >= 0.5], spb, 0.45, 0.3, overlap=0.04)

    bass_ev, chord_ev, harp_ev = [], [], []
    for bi, c in enumerate(prog):
        b0 = bi * 4
        r2 = root_in(c, "E2")
        r3, t3 = chord(c, 3)
        fifth = r2 + 7
        sec_b = 8 <= bi < 16
        sec_a2 = bi >= 16
        # walking pizzicato bass: root on 1, fifth on 3 (+ passing note on 4& in A')
        for k, m in ((0, r2), (2, fifth if fifth <= 52 else fifth - 12)):
            mx.add("pizz", o.vc_pizz.render(fit(o.vc_pizz, m + 12), None, 0.8), b0 + k, pan=0.3, humanize=H, rng=rng)
            mx.add("pizz", o.cb_pizz.render(fit(o.cb_pizz, m), None, 0.75), b0 + k, pan=0.35, humanize=H, rng=rng)
            bass_ev.append((b0 + k, 1, m))
        # afterbeat pizzicato chords (violas + violins)
        for k in (1, 3) if not sec_a2 else (1, 1.5, 3, 3.5):
            v = 0.55 if k in (1, 3) else 0.4
            for m in t3[1:]:
                mx.add("pizz", o.va_pizz.render(fit(o.va_pizz, m + 12), None, v), b0 + k, pan=0.1, humanize=H, rng=rng)
            mx.add("pizz", o.vs_pizz.render(fit(o.vs_pizz, t3[0] + 24), None, v * 0.9), b0 + k, pan=-0.4,
                   humanize=H, rng=rng)
            chord_ev.append((b0 + k, 0.5, t3[1] + 12))
        # harp 8th arpeggios in B, bassoon line holding roots
        if sec_b:
            a = chord(c, 4)[1]
            for k in range(8):
                m = [a[0] - 12, a[1] - 12, a[2] - 12, a[0], a[1], a[2], a[0], a[2] - 12][k]
                mx.add("harp", o.harp.render(m, None, 0.45), b0 + k * 0.5, pan=0.45, humanize=H * 0.5, rng=rng)
                harp_ev.append((b0 + k * 0.5, 0.5, m))
            mx.add("wind2", o.bn.render(fit(o.bn, r2 + 12), 4 * spb, 0.5, release=0.4), b0, pan=0.25, rng=rng)
        # sustained warmth: horns in B and A', soft string pad in A'
        if sec_b or sec_a2:
            for m in t3[:2]:
                mx.add("pad", o.hn_sus.render(fit(o.hn_sus, m), 4 * spb, 0.35, release=0.5), b0, pan=-0.15, rng=rng)
        if sec_a2:
            mx.add("pad", o.va_sus.render(fit(o.va_sus, t3[2] + 12), 4 * spb, 0.35, release=0.5), b0, pan=0.15, rng=rng)
        # light percussion
        if bi % 2 == 0:
            mx.add("perc", o.tri.render(vel=0.35), b0, pan=0.4)
        if sec_a2:
            for k in (1, 3):
                mx.add("perc", o.tamb_shake.render(vel=0.3), b0 + k, pan=-0.3, humanize=H, rng=rng)
    mx.add("perc", o.crash.render(vel=0.3), 64, pan=0.35)
    place_swell(mx, "perc", o.cym_swell.render(vel=0.25), 64)

    gains = {"melody": 1.0, "wind2": 0.7, "pizz": 0.6, "harp": 0.65, "pad": 0.5, "perc": 0.45}
    wet = {"melody": 0.3, "wind2": 0.3, "pizz": 0.2, "harp": 0.35, "pad": 0.4, "perc": 0.3}
    loop_n = int(round(loop_s * SR))
    x = mixdown(mx, gains, wet, loop_n=loop_n, ir_decay=0.6, drive=1.0)
    export("dawnweaver_field_real_loop", x, loop_n, "灯の谷を渡る風 (Field)")
    write_midi(os.path.join(OUT, "dawnweaver_field_real.mid"), bpm,
               [("Melody", 73, 0, A + B + A2), ("Clarinet", 71, 1, under), ("Pizz Bass", 45, 2, bass_ev),
                ("Pizz Chords", 45, 3, chord_ev), ("Harp", 46, 4, harp_ev)])


if __name__ == "__main__":
    which = sys.argv[1:] or ["title", "field"]
    orch = extra(Orchestra())
    if "title" in which:
        title(orch)
    if "field" in which:
        field(orch)
