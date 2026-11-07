"""Dawn Weaver battle variations: violin-led and guitar-led.

Run:  python songs2.py [violin] [guitar]
"""
import os
from synth import *  # noqa: F401,F403
from songs import OUT, chord, export, render


def root_in(name, lo="E2"):
    """Root note of a chord placed in [lo, lo+11] (guitar/bass register)."""
    r = chord(name, 2)[0]
    while r < midi_of(lo):
        r += 12
    while r >= midi_of(lo) + 12:
        r -= 12
    return r


def run(notes, start, step=0.25):
    return [(start + i * step, step, midi_of(n)) for i, n in enumerate(notes.split())]


# =====================================================================
# 4) Violin battle  "糸車の剣舞"  A minor, 168 BPM, 24 bars loop
# =====================================================================
def violin_battle():
    bpm, nbars = 168, 24
    spb = 60 / bpm
    loop_s = nbars * 4 * spb
    mx = Mix(loop_s + 4.0, bpm)
    prog = ["Am", "F", "G", "Am", "Am", "F", "G", "E",
            "Dm", "G", "C", "Am", "Dm", "F", "E", "E",
            "Am", "G", "F", "E", "Am", "G", "F", "E7"]
    mel = parse_line(" ".join([
        "E5:.5 A5:.5 B5:.5 C6:.5 B5:.5 A5:.5 E5:1", "F5:.5 A5:.5 C6:1 B5:.5 A5:.5 F5:1",
        "G5:.5 B5:.5 D6:1 C6:.5 B5:.5 G5:1", "A5:2.5 C6:.5 B5:.5 A5:.5",
        "E6:1 D6:.5 C6:.5 B5:.5 A5:.5 C6:1", "D6:1 C6:.5 A5:.5 F5:1 A5:1",
        "B5:.5 C6:.5 D6:.5 B5:.5 G5:1 D5:1", "E5:.25 F5:.25 G#5:.25 A5:.25 B5:.5 G#5:.5 E5:2",
        "F5:1.5 A5:.5 D6:2", "D6:.5 C6:.5 B5:.5 A5:.5 G5:2", "E5:.5 G5:.5 C6:1.5 B5:.5 C6:1", "A5:3 r:1",
        "F5:.5 A5:.5 D6:1 F6:1.5 E6:.5", "D6:1 C6:.5 A5:.5 F5:2", "E5:.5 G#5:.5 B5:.5 D6:.5 E6:2",
        "E6:.25 D6:.25 C6:.25 B5:.25 A5:.25 G#5:.25 F5:.25 E5:.25 D5:.5 E5:.5 G#5:1",
    ]))
    # C section: 16th-note runs
    mel += run("A5 C6 E6 C6 A5 C6 E6 A6", 64) + parse_line("G6:.5 E6:.5 A6:1", 66)
    mel += run("G5 B5 D6 B5 G5 B5 D6 G6", 68) + parse_line("F6:.5 D6:.5 G6:1", 70)
    mel += run("F5 A5 C6 A5 F5 A5 C6 F6", 72) + parse_line("E6:.5 C6:.5 F6:1", 74)
    mel += parse_line("E6:1 D6:.5 C6:.5 B5:1 G#5:1 "
                      "A6:1.5 E6:.5 C6:1 A5:1 B5:1.5 D6:.5 G6:2 A6:1 G6:.5 F6:.5 E6:1 C6:1", 76)
    mel += run("B5 C6 B5 A5 G#5 A5 B5 D6", 92) + parse_line("E6:.5 D6:.5 B5:.5 G#5:.5", 94)

    for b, d, m in mel:
        mx.add("vln", violin(hz(m), d * spb, 0.9, short=d <= 0.25), b, pan=0.1)
    # second violin a 6th/3rd below in B section for a duet feel
    duet = [(b, d, m - (9 if m % 12 in (0, 4, 5, 9) else 8)) for b, d, m in mel if 32 <= b < 64]
    for b, d, m in duet:
        mx.add("vln2", violin(hz(m), d * spb, 0.6, short=d <= 0.25), b, pan=-0.35)

    bass_ev, stacc_ev, pad_ev, harp_ev = [], [], [], []
    for bi, c in enumerate(prog):
        b0 = bi * 4
        r = root_in(c, "E2")
        for k in range(8):  # cello/bass spiccato 8ths with octave pops
            bass_ev.append((b0 + k * 0.5, 0.4, r + (12 if k in (2, 6) else 0)))
        tones = chord(c, 4)[1][:3]
        for k in range(8):
            if k % 2 == 1 or bi >= 16:
                for m in tones:
                    stacc_ev.append((b0 + k * 0.5, 0.25, m))
        for m in chord(c, 3)[1][:3]:
            pad_ev.append((b0, 4, m))
        if 8 <= bi < 16:
            a = chord(c, 4)[1][:3]
            for k in range(8):
                harp_ev.append((b0 + k * 0.5, 0.5, [a[0], a[1], a[2], a[0] + 12][k % 4]))
    mx.notes("bass", bass, bass_ev, vel=0.8)
    mx.notes("bass", strings_stacc, [(b, d, m + 12) for b, d, m in bass_ev], pan=-0.2, vel=0.4, bright=2500)
    mx.notes("strings", strings_stacc, stacc_ev, pan=0.4, vel=0.45)
    mx.notes("pad", strings_legato, pad_ev, pan=-0.3, vel=0.38, bright=2200)
    mx.notes("harp", pluck, harp_ev, pan=0.5, vel=0.5)

    for bi in range(nbars):
        b0 = bi * 4
        for k in (0, 2, 2.5):
            mx.add("drums", kick(0.85), b0 + k)
        for k in (1, 3):
            mx.add("drums", snare(0.65), b0 + k, pan=0.05)
        for k in range(16):  # tambourine-like 16ths
            mx.add("drums", hat(0.55 if k % 4 == 2 else 0.25), b0 + k * 0.25, pan=0.3)
        if bi % 8 == 0:
            mx.add("drums", crash(0.8), b0, pan=-0.4)
        if bi % 8 == 7:
            for k in range(4):
                mx.add("drums", snare(0.4 + 0.12 * k), b0 + 3 + k * 0.25)
        if bi % 4 == 0 or bi % 8 == 7:
            r = root_in(prog[bi], "F2")
            mx.add("timp", timpani(hz(r), 0.8), b0)

    stereo = render(mx, {"vln": 1.0, "vln2": 0.8, "bass": 0.7, "strings": 0.5, "pad": 0.5,
                         "harp": 0.45, "drums": 0.6, "timp": 0.55},
                    wet={"vln": 0.3, "vln2": 0.3, "strings": 0.2, "pad": 0.35, "harp": 0.35,
                         "drums": 0.1, "timp": 0.25, "bass": 0.05})
    loop_n = int(round(loop_s * SR))
    out = master(fold_loop(stereo, loop_n))
    export("dawnweaver_battle_violin_loop", out, loop_n, "糸車の剣舞 (Violin Battle)")
    write_midi(os.path.join(OUT, "dawnweaver_battle_violin.mid"), bpm,
               [("Violin", 40, 0, mel), ("Violin 2", 40, 1, duet), ("Cello/Bass", 42, 2, bass_ev),
                ("Staccato Strings", 45, 3, stacc_ev), ("Pad", 48, 4, pad_ev), ("Harp", 46, 5, harp_ev)])


# =====================================================================
# 5) Guitar battle  "灰の峠を駆ける"  E minor, 160 BPM, 24 bars loop
# =====================================================================
def guitar_battle():
    bpm, nbars = 160, 24
    spb = 60 / bpm
    loop_s = nbars * 4 * spb
    mx = Mix(loop_s + 4.0, bpm)
    prog = ["Em", "C", "D", "Em", "Em", "C", "D", "B",
            "Am", "C", "G", "D", "Am", "C", "B", "B",
            "Em", "D", "C", "B", "Em", "D", "C", "B"]
    mel = parse_line(" ".join([
        "E5:1.5 B4:.5 E5:.5 F#5:.5 G5:1", "G5:.5 F#5:.5 E5:1 C5:1 E5:1",
        "F#5:1.5 D5:.5 A5:1 F#5:1", "G5:.5 F#5:.5 E5:3",
        "B5:1.5 A5:.5 G5:1 B5:1", "C6:1 B5:.5 A5:.5 G5:1 E5:1",
        "D5:.5 E5:.5 F#5:.5 A5:.5 D6:1 C6:.5 A5:.5", "B5:4",
        "A5:.5 B5:.5 C6:1 E6:1 C6:1", "G5:.5 A5:.5 G5:1 E5:1 G5:1",
        "B5:1 D6:1 G6:1.5 F#6:.5", "F#6:2 D6:1 A5:1",
        "C6:1.5 B5:.5 A5:1 E6:1", "E6:1 D6:.5 C6:.5 G5:2",
        "F#5:.5 A5:.5 B5:.5 D#6:.5 F#6:2", "F#6:.5 E6:.5 D#6:.5 B5:.5 A5:.5 F#5:.5 D#5:1",
    ]))
    mel += run("E5 G5 B5 E6 B5 G5 E5 G5 E5 G5 B5 E6 B5 G5 E5 G5", 64)
    mel += run("D5 F#5 A5 D6 A5 F#5 D5 F#5 D5 F#5 A5 D6 A5 F#5 D5 F#5", 68)
    mel += run("C5 E5 G5 C6 G5 E5 C5 E5", 72) + parse_line("E6:1 G6:1", 74)
    mel += parse_line("F#6:1 D#6:1 B5:1 F#5:.5 A5:.5 "
                      "G6:1.5 F#6:.5 E6:1 B5:1 A5:.5 B5:.5 D6:1 F#6:1.5 E6:.5 "
                      "E6:1 D6:.5 C6:.5 G5:1 E6:1", 76)
    mel += run("D#6 E6 F#6 E6 D#6 B5 A5 F#5", 92) + parse_line("D#5:1 B4:1", 94)

    for b, d, m in mel:
        mx.add("lead", guitar_lead(hz(m), d * spb, 0.9), b, pan=0.05)

    rhythm, bass_ev, pad_ev = [], [], []
    for bi, c in enumerate(prog):
        b0 = bi * 4
        r = root_in(c, "E2")
        section_c = bi >= 16
        # palm-muted 8ths with open accents on the 3+3+2 pulse
        for k in range(8):
            open_ = k in (0, 3, 6)
            rhythm.append((b0 + k * 0.5, 1.5 if open_ and k == 6 else (0.5 if open_ else 0.25), r, not open_))
        if section_c:  # extra 16th gallop in the solo section
            for k in (1, 5):
                rhythm.append((b0 + k * 0.5 + 0.25, 0.2, r, True))
        for k in range(8):
            bass_ev.append((b0 + k * 0.5, 0.45, r - 12 if r - 12 >= midi_of("E1") else r))
        for m in chord(c, 4)[1][:3]:
            pad_ev.append((b0, 4, m))
    for side, pan in ((0, -0.7), (1, 0.7)):  # double-tracked rhythm guitars
        for b, d, m, mute in rhythm:
            off = 0.004 * side  # tiny timing offset for width
            mx.add("rhythm", guitar_power(hz(m), d * spb, 0.8 if mute else 1.0, mute=mute), b + off, pan=pan)
    mx.notes("bass", bass, bass_ev, vel=0.95)
    mx.notes("pad", strings_legato, pad_ev, pan=0.0, vel=0.3, bright=2500)
    mx.notes("pad", organ, [(b, d, m) for b, d, m in pad_ev if b >= 64], pan=0.0, vel=0.5)

    for bi in range(nbars):
        b0 = bi * 4
        for k in (0, 1.5, 2, 3):
            mx.add("drums", kick(1.0), b0 + k)
        if bi >= 16:
            for k in (0.5, 2.5, 3.5):
                mx.add("drums", kick(0.75), b0 + k)
        for k in (1, 3):
            mx.add("drums", snare(1.0), b0 + k, pan=0.05)
        for k in range(8):
            mx.add("drums", hat(0.6 if k % 2 == 0 else 0.4, open_=(k == 7 and bi % 2)), b0 + k * 0.5, pan=-0.3)
        if bi % 8 == 0:
            mx.add("drums", crash(1.0), b0, pan=0.45)
        elif bi % 4 == 0:
            mx.add("drums", crash(0.6), b0, pan=-0.45)
        if bi % 8 == 7:
            for k in range(8):
                mx.add("drums", snare(0.5 + 0.06 * k), b0 + 2 + k * 0.25, pan=-0.2 + 0.05 * k)

    stereo = render(mx, {"lead": 1.0, "rhythm": 0.55, "bass": 0.75, "pad": 0.4, "drums": 0.8},
                    wet={"lead": 0.22, "rhythm": 0.06, "pad": 0.35, "drums": 0.08, "bass": 0.0},
                    ir_decay=0.45)
    loop_n = int(round(loop_s * SR))
    out = master(fold_loop(stereo, loop_n), drive=1.6)
    export("dawnweaver_battle_guitar_loop", out, loop_n, "灰の峠を駆ける (Guitar Battle)")
    write_midi(os.path.join(OUT, "dawnweaver_battle_guitar.mid"), bpm,
               [("Lead Guitar", 29, 0, mel), ("Rhythm Guitar", 30, 1, [(b, d, m) for b, d, m, _ in rhythm]),
                ("Bass", 33, 2, bass_ev), ("Pad", 48, 3, pad_ev)])


if __name__ == "__main__":
    import sys
    which = sys.argv[1:] or ["violin", "guitar"]
    if "violin" in which:
        violin_battle()
    if "guitar" in which:
        guitar_battle()
