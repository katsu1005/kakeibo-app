"""Boss battle and victory fanfare re-orchestrated with recorded instruments (VSCO 2 CE, CC0).

Run:  python orchestral_real.py [boss] [victory]
"""
import os
import sys
import numpy as np
from synth import SR, midi_of, parse_line, make_ir, reverb, fold_loop, write_midi, hp
from sampler import Instrument, StereoMix
from songs import OUT, chord, export
from songs2 import root_in

rng = np.random.default_rng(23)
H = 0.006  # timing humanize (s)


class Orchestra:
    def __init__(self):
        I = Instrument
        self.vs_sus = I("Strings/Violin Section/susVib")
        self.vs_spic = I("Strings/Violin Section/Spic")
        self.vs_trem = I("Strings/Violin Section/Trem")
        self.va_spic = I("Strings/Viola Section/spic")
        self.va_sus = I("Strings/Viola Section/susvib")
        self.vc_sus = I("Strings/Cello Section/susvib")
        self.vc_spic = I("Strings/Cello Section/spic")
        self.vc_trem = I("Strings/Cello Section/trem")
        self.cb_spic = I("Strings/Solo Contrabass/Spic")
        self.cb_sus = I("Strings/Solo Contrabass/SusVib")
        self.harp = I("Strings/Harp")
        self.hn_sus = I("Brass/F Horn/sus")
        self.hn_stac = I("Brass/F Horn/stac")
        self.tb_sus = I("Brass/Tenor Trombone/sus")
        self.tb_stac = I("Brass/Tenor Trombone/stac")
        self.tp_sus = I("Brass/Trumpet/sus")
        self.tp_stac = I("Brass/Trumpet/stac")
        self.tu_sus = I("Brass/Tuba/sus")
        self.tu_stac = I("Brass/Tuba/stac")
        self.fl = I("Woodwinds/Flute/susvib")
        self.glock = I("Percussion/Glock")
        self.timp = I("Percussion/Timpani", pattern=r"^Timpani1_Hit", pitched=False)
        self.timp.pitched = True
        for s in self.timp.samples:
            s["midi"] = 41.4  # measured fundamental of drum 1 (~89.5 Hz)
        self.timp_roll = I("Percussion/Timpani/Rolls", pattern=r"^Timpani1_Roll", pitched=False)
        self.timp_roll.pitched = True
        for s in self.timp_roll.samples:
            s["midi"] = 41.4
        self.bdrum = I("Percussion", pattern=r"^BDrumNewhit", pitched=False)
        self.snare = I("Percussion", pattern=r"^Snare2-HitSN", pitched=False)
        self.snare_roll = I("Percussion", pattern=r"^Snare2-rollSN", pitched=False)
        self.crash = I("Percussion", pattern=r"^cymbal-crash1_(mf|ff)", pitched=False)
        self.swell = I("Percussion", pattern=r"^susCymb1-cresc-Median", pitched=False)
        self.gong = I("Percussion", pattern=r"^gongHit_(f|fff)\.wav", pitched=False)


def fit(inst, m):
    """Move a note by octaves into an instrument's sampled range (+-3 semitone tolerance)."""
    lo = min(s["midi"] for s in inst.samples) - 3
    hi = max(s["midi"] for s in inst.samples) + 3
    while m > hi:
        m -= 12
    while m < lo:
        m += 12
    return m


def sus(mx, bus, inst, notes, spb, vel, pan, release=0.25):
    for b, d, m in notes:
        mx.add(bus, inst.render(fit(inst, m), d * spb + 0.04, vel, release=release), b, pan=pan,
               humanize=H, rng=rng)


def mixdown(mx, gains, wet, loop_n=None, ir_decay=0.55, tail_s=None, drive=1.15):
    ir = make_ir(seconds=2.6, decay=ir_decay)
    total = None
    for name, b in mx.buses.items():
        sig = reverb(b * gains.get(name, 1.0), wet.get(name, 0.0), ir)
        total = sig if total is None else total + sig
    if loop_n is not None:
        x = fold_loop(total, loop_n)
    else:
        x = total[:, : int(tail_s * SR)]
        fade = int(1.4 * SR)
        x[:, -fade:] *= np.linspace(1, 0, fade) ** 2
    x = hp(x, 30, 2)
    x = x / np.max(np.abs(x))
    x = np.tanh(x * drive) / np.tanh(drive)
    return x / np.max(np.abs(x)) * 0.89


# =====================================================================
# Boss  "黎明を喰らうもの"  C minor, 172 BPM, 32 bars
# =====================================================================
def boss(o):
    bpm, nbars = 172, 32
    spb = 60 / bpm
    loop_s = nbars * 4 * spb
    mx = StereoMix(loop_s + 6.0, bpm)
    prog = ["Cm", "Cm", "Ab", "G",
            "Cm", "Ab", "Fm", "G", "Cm", "Db", "Bb", "G",
            "Ab", "Bb", "Gm", "Cm", "Fm", "Db", "Eb", "G",
            "Cm", "Bb", "Ab", "G", "Fm", "Ab", "G", "G",
            "Cm", "Db", "Cm", "G"]
    A = parse_line(" ".join([
        "C5:1.5 G4:.5 C5:1 Eb5:1", "D5:1.5 Eb5:.5 C5:2", "F5:1 Eb5:.5 D5:.5 C5:1 Ab4:1", "B4:3 G4:1",
        "C5:1.5 G4:.5 C5:1 Eb5:1", "F5:1.5 Eb5:.5 Db5:2", "D5:1 F5:1 Bb5:1.5 Ab5:.5", "G5:4"]), 16)
    B = parse_line(" ".join([
        "Eb5:1 C5:1 Ab5:2", "F5:1 D5:1 Bb5:2", "G5:1.5 F5:.5 D5:1 Bb4:1", "C5:3 Eb5:1",
        "F5:1 Ab5:1 C6:2", "Db6:1.5 C6:.5 Ab5:2", "Bb5:1 G5:1 Eb5:1 Bb5:1", "B5:2 D6:2"]), 48)
    C = parse_line(" ".join([
        "C6:2 G5:1 Eb5:1", "D6:1.5 Bb5:.5 F5:2", "Eb6:1.5 C6:.5 Ab5:1 C6:1", "B5:2 G5:1 B5:1",
        "Ab5:1 C6:1 F6:1.5 Eb6:.5", "Eb6:1 C6:1 Ab5:1 Eb5:1", "D5:1 G5:1 B5:1 D6:1", "F6:1 Eb6:1 D6:1 B5:1"]), 80)

    # --- melodies
    down = lambda ev, k: [(b, d, m - k) for b, d, m in ev]
    # A: horns + trombones in unison an octave down (heroic-dark), trumpets on top softly
    sus(mx, "brass", o.hn_sus, down(A, 12), spb, 0.85, -0.3)
    sus(mx, "brass", o.tb_sus, down(A, 12), spb, 0.8, 0.25)
    sus(mx, "brass", o.tp_sus, A, spb, 0.45, 0.1)
    # B: violins carry the line, flutes an octave up, cellos an octave down
    sus(mx, "strings", o.vs_sus, B, spb, 0.85, -0.35, release=0.3)
    sus(mx, "strings", o.vc_sus, down(B, 12), spb, 0.6, 0.35, release=0.3)
    sus(mx, "wind", o.fl, [(b, d, m + 12) for b, d, m in B], spb, 0.5, 0.25)
    # C: tutti
    sus(mx, "strings", o.vs_sus, C, spb, 1.0, -0.35, release=0.3)
    sus(mx, "brass", o.tp_sus, down(C, 12), spb, 0.95, 0.1)
    sus(mx, "brass", o.hn_sus, down(C, 12), spb, 0.85, -0.3)
    sus(mx, "brass", o.tb_sus, down(C, 24), spb, 0.85, 0.3)
    sus(mx, "wind", o.fl, C, spb, 0.55, 0.25)

    ost_ev, bass_ev, hit_ev, pad_ev = [], [], [], []
    patt = [0, 0, 7, 0, 0, 7, 12, 7]
    for bi, c in enumerate(prog):
        b0 = bi * 4
        r3, tones3 = chord(c, 3)
        r2 = root_in(c, "C2")
        intro_break = bi < 4 or bi >= 28
        # 16th-note ostinato: violas + 2nd violins (spiccato), accents on 3+3+2
        for k in range(16):
            iv = patt[k % 8]
            if k % 8 == 4 and bi % 2:
                iv = tones3[1] - r3
            m = r3 + iv + 12
            acc = k % 8 in (0, 3, 6)
            v = (0.85 if acc else 0.55) * (0.8 if intro_break else (0.7 if 12 <= bi < 20 else 1.0))
            mx.add("ost", o.va_spic.render(fit(o.va_spic, m), None, v), b0 + k * 0.25, pan=0.3, humanize=H * 0.5, rng=rng)
            if not intro_break:
                mx.add("ost", o.vs_spic.render(fit(o.vs_spic, m + 12), None, v * 0.8), b0 + k * 0.25, pan=-0.45,
                       humanize=H * 0.5, rng=rng)
            ost_ev.append((b0 + k * 0.25, 0.2, m))
        # low strings + tuba on the 3+3+2 pulse
        for k in (0, 1.5, 3):
            mx.add("low", o.vc_spic.render(fit(o.vc_spic, r2 + 12), None, 0.9), b0 + k, pan=0.35, humanize=H, rng=rng)
            mx.add("low", o.cb_spic.render(fit(o.cb_spic, r2), None, 0.95), b0 + k, pan=0.4, humanize=H, rng=rng)
            bass_ev.append((b0 + k, 0.5, r2))
        if not (12 <= bi < 20):
            for k in (0, 1.5, 3):
                mx.add("low", o.tu_stac.render(fit(o.tu_stac, r2), None, 0.8), b0 + k, pan=0.15, humanize=H, rng=rng)
        # brass stabs (horns + trombones) on 3+3+2 in intro, A and C
        if bi < 12 or 20 <= bi < 28:
            for k in (0, 1.5, 3):
                for m in tones3:
                    v = 0.75 if bi >= 4 else 0.6
                    mx.add("stab", o.hn_stac.render(fit(o.hn_stac, m + 12), None, v), b0 + k, pan=-0.3, humanize=H, rng=rng)
                    mx.add("stab", o.tb_stac.render(fit(o.tb_stac, m), None, v), b0 + k, pan=0.3, humanize=H, rng=rng)
                    hit_ev.append((b0 + k, 0.4, m))
        # tension bed: string tremolo (intro / B / break), held horn chords in B
        if intro_break or 12 <= bi < 20:
            for m in chord(c, 4)[1]:
                mx.add("pad", o.vs_trem.render(fit(o.vs_trem, m + 12), 4 * spb, 0.5, release=0.3), b0, pan=-0.2, rng=rng)
            mx.add("pad", o.vc_trem.render(fit(o.vc_trem, r2 + 12), 4 * spb, 0.6, release=0.3), b0, pan=0.3, rng=rng)
        if 12 <= bi < 20:
            for m in tones3:
                mx.add("pad", o.hn_sus.render(fit(o.hn_sus, m + 12), 4 * spb, 0.45, release=0.4), b0, pan=-0.3, rng=rng)
        if bi >= 28:  # break: low brass chorale swells
            for m in (r2 + 12, tones3[1], tones3[2]):
                mx.add("pad", o.tb_sus.render(fit(o.tb_sus, m), 4 * spb, 0.55, release=0.5), b0, pan=0.2, rng=rng)
            mx.add("pad", o.tu_sus.render(fit(o.tu_sus, r2), 4 * spb, 0.6, release=0.5), b0, pan=0.1, rng=rng)
        for m in tones3:
            pad_ev.append((b0, 4, m))

    # --- percussion
    for bi in range(nbars):
        b0 = bi * 4
        c = prog[bi]
        intro_break = bi < 4 or bi >= 28
        for k in (0, 1.5, 3):
            mx.add("perc", o.bdrum.render(vel=0.95 if k == 0 else 0.75), b0 + k, pan=-0.05)
        if not intro_break:
            for k in (1, 3):
                mx.add("perc", o.snare.render(vel=0.8), b0 + k, pan=0.1, humanize=H, rng=rng)
        if bi in (4, 12, 20):
            mx.add("perc", o.crash.render(vel=0.95), b0, pan=0.4)
            mx.add("perc", o.crash.render(vel=0.8), b0, pan=-0.4)
        if bi in (0, 28):
            mx.add("perc", o.gong.render(vel=0.9), b0, pan=0.2)
        r = root_in(c, "F2")
        mx.add("timp", o.timp.render(r, 1.2, 0.95, release=0.4), b0, pan=-0.2)
        if bi % 4 == 3:
            mx.add("timp", o.timp_roll.render(r, 2 * spb, 0.8, release=0.1, fade_in=0.4), b0 + 2, pan=-0.2)
    sr_ = o.snare_roll.render(vel=0.9)
    mx.add("perc", sr_[:, : int(4 * spb * SR)] * np.linspace(0.3, 1.2, int(4 * spb * SR)), 31 * 4, pan=0.1)
    sw = o.swell.render(vel=0.9)
    mx.add("perc", sw, 32 * 4 - sw.shape[1] / SR / spb, pan=0.0)

    gains = {"brass": 1.0, "strings": 1.0, "wind": 0.9, "ost": 0.5, "low": 0.6, "stab": 0.5,
             "pad": 0.45, "perc": 0.65, "timp": 0.8}
    wet = {"brass": 0.28, "strings": 0.28, "wind": 0.3, "ost": 0.15, "low": 0.12, "stab": 0.22,
           "pad": 0.35, "perc": 0.18, "timp": 0.25}
    loop_n = int(round(loop_s * SR))
    x = mixdown(mx, gains, wet, loop_n=loop_n, ir_decay=0.7, drive=1.3)
    export("dawnweaver_battle_boss_real_loop", x, loop_n, "黎明を喰らうもの (Boss Battle, recorded orchestra)")
    write_midi(os.path.join(OUT, "dawnweaver_battle_boss_real.mid"), bpm,
               [("Melody", 60, 0, A + B + C), ("Ostinato", 45, 1, ost_ev), ("Low", 42, 2, bass_ev),
                ("Brass Stabs", 61, 3, hit_ev), ("Pad", 48, 4, pad_ev)])
    return mx


# =====================================================================
# Victory  "夜明けの糸"  D major, 132 BPM
# =====================================================================
def victory(o):
    bpm = 132
    spb = 60 / bpm
    total_beats = 12
    tail = total_beats * spb + 3.4
    mx = StereoMix(tail + 3.0, bpm)
    mel = parse_line("A4:.5 D5:.5 F#5:.5 A5:.5 G5:1 B5:1 A5:1 E5:.5 A5:.5 C#6:1 E6:1 D6:4")
    # trumpets on the tune, horns an octave down, violins double
    for b, d, m in mel:
        stac = d <= 0.5
        if stac:
            mx.add("brass", o.tp_stac.render(fit(o.tp_stac, m), None, 0.9), b, pan=0.1, humanize=H * 0.5, rng=rng)
            mx.add("brass", o.hn_stac.render(fit(o.hn_stac, m - 12), None, 0.8), b, pan=-0.3, humanize=H * 0.5, rng=rng)
        else:
            mx.add("brass", o.tp_sus.render(fit(o.tp_sus, m), d * spb + 0.05, 0.95, release=0.35), b, pan=0.1, rng=rng)
            mx.add("brass", o.hn_sus.render(fit(o.hn_sus, m - 12), d * spb + 0.05, 0.85, release=0.35), b, pan=-0.3, rng=rng)
        mx.add("strings", o.vs_sus.render(fit(o.vs_sus, m), d * spb + 0.05, 0.6 if stac else 0.75, release=0.3),
               b, pan=-0.4, rng=rng)
    harm = [(0, "D", 2), (2, "G", 2), (4, "Em", 2), (6, "A7", 2), (8, "D", 4)]
    pad_ev, bass_ev = [], []
    for b, c, d in harm:
        r, tones = chord(c, 3)
        last = b >= 8
        dd = (4.5 if last else d) * spb
        for m in tones[:3]:
            mx.add("brass", o.tb_sus.render(fit(o.tb_sus, m), dd, 0.7 if last else 0.6, release=0.6), b, pan=0.3, rng=rng)
            mx.add("strings", o.va_sus.render(fit(o.va_sus, m + 12), dd, 0.55, release=0.5), b, pan=0.2, rng=rng)
            pad_ev.append((b, d, m))
        rb = root_in(c, "D2")
        mx.add("low", o.vc_sus.render(fit(o.vc_sus, rb + 12), dd, 0.7, release=0.5), b, pan=0.35, rng=rng)
        mx.add("low", o.tu_sus.render(fit(o.tu_sus, rb), dd, 0.65, release=0.5), b, pan=0.1, rng=rng)
        bass_ev.append((b, d, rb))
    # final chord colour: flute on top, harp glissando, glockenspiel sparkle
    mx.add("wind", o.fl.render(fit(o.fl, midi_of("A6")), 4.5 * spb, 0.55, release=0.6), 8, pan=0.3, rng=rng)
    mx.add("wind", o.fl.render(fit(o.fl, midi_of("F#6")), 4.5 * spb, 0.5, release=0.6), 8, pan=0.35, rng=rng)
    scale = ["D4", "E4", "F#4", "A4", "B4", "D5", "E5", "F#5", "A5", "B5", "D6", "E6", "F#6", "A6"]
    harp_ev = []
    for i, n in enumerate(scale):
        mx.add("harp", o.harp.render(midi_of(n), None, 0.5 + 0.02 * i), 7.4 + i * 0.045, pan=0.45)
        harp_ev.append((7.4 + i * 0.045, 1, midi_of(n)))
    for n, t in (("D6", 8), ("A6", 8.5), ("D7", 9)):
        mx.add("harp", o.glock.render(fit(o.glock, midi_of(n)), None, 0.45), t, pan=0.25)
    # percussion
    mx.add("timp", o.timp.render(root_in("D", "F2"), 1.5, 0.9, release=0.4), 0, pan=-0.2)
    mx.add("timp", o.timp_roll.render(root_in("A", "F2"), 2 * spb, 0.85, release=0.05, fade_in=0.3), 6, pan=-0.2)
    mx.add("timp", o.timp.render(root_in("D", "F2"), 2.5, 1.0, release=0.8), 8, pan=-0.2)
    mx.add("perc", o.snare.render(vel=0.7), 0, pan=0.1)
    mx.add("perc", o.bdrum.render(vel=0.8), 0)
    mx.add("perc", o.bdrum.render(vel=0.95), 8)
    mx.add("perc", o.crash.render(vel=1.0), 8, pan=0.4)
    mx.add("perc", o.crash.render(vel=0.85), 8, pan=-0.4)
    sw = o.swell.render(vel=0.7)
    mx.add("perc", sw, 8 - sw.shape[1] / SR / spb, pan=0.0)

    gains = {"brass": 1.0, "strings": 0.75, "low": 0.6, "wind": 0.9, "harp": 1.0, "perc": 0.6, "timp": 0.8}
    wet = {"brass": 0.3, "strings": 0.32, "low": 0.2, "wind": 0.35, "harp": 0.4, "perc": 0.22, "timp": 0.3}
    x = mixdown(mx, gains, wet, tail_s=tail, ir_decay=0.65, drive=1.1)
    export("dawnweaver_victory_fanfare_real", x, None, "夜明けの糸 (Victory, recorded orchestra)")
    write_midi(os.path.join(OUT, "dawnweaver_victory_fanfare_real.mid"), bpm,
               [("Trumpet", 56, 0, mel), ("Brass/Strings", 48, 1, pad_ev), ("Low", 58, 2, bass_ev),
                ("Harp", 46, 3, harp_ev)])
    return mx


if __name__ == "__main__":
    which = sys.argv[1:] or ["boss", "victory"]
    orch = Orchestra()
    if "boss" in which:
        boss(orch)
    if "victory" in which:
        victory(orch)
