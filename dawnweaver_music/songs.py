"""Dawn Weaver battle music: normal battle, boss battle, victory fanfare.

Run:  python songs.py   (writes WAV / MP3 / MIDI into ./out)
"""
import os
import subprocess
import numpy as np
from synth import *  # noqa: F401,F403

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

QUAL = {"": [0, 4, 7], "m": [0, 3, 7], "7": [0, 4, 7, 10], "sus4": [0, 5, 7]}


def chord(name, octave=3):
    root = name[0]
    i = 1
    if len(name) > 1 and name[1] in "#b":
        i = 2
    q = name[i:]
    r = midi_of(name[:i] + str(octave))
    return r, [r + s for s in QUAL[q]]


def bars(prog, beats_per_chord=4):
    """['Dm','Bb'] -> [(beat, chordname)]"""
    return [(i * beats_per_chord, c) for i, c in enumerate(prog)]


def export(name, mix_stereo, loop_n=None, title=""):
    wav = os.path.join(OUT, name + ".wav")
    mp3 = os.path.join(OUT, name + ".mp3")
    ogg = os.path.join(OUT, name + ".ogg")
    write_wav(wav, mix_stereo)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "192k",
                    "-metadata", f"title={title}", "-metadata", "artist=Dawn Weaver OST",
                    mp3], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "6",
                    "-metadata", f"title={title}", ogg], check=True)
    print(name, f"{mix_stereo.shape[1] / SR:.2f}s")


# =====================================================================
# 1) Normal battle  "朝霧を織る刃"  D minor, 156 BPM, 24 bars loop
# =====================================================================
def normal_battle():
    bpm = 156
    nbars = 24
    loop_beats = nbars * 4
    spb = 60 / bpm
    loop_s = loop_beats * spb
    mx = Mix(loop_s + 4.0, bpm)

    prog = ["Dm", "Bb", "C", "Dm", "Dm", "Bb", "Gm", "A",
            "Bb", "C", "Am", "Dm", "Gm", "C", "F", "A",
            "F", "C", "Dm", "Bb", "Gm", "Bb", "A", "A7"]
    melody = " ".join([
        # A
        "A4:1.5 D5:.5 E5:1 F5:1", "G5:1.5 F5:.5 D5:2", "E5:1 C5:.5 D5:.5 E5:1 G5:1", "A5:3 r:1",
        "A5:1.5 G5:.5 F5:1 A5:1", "Bb5:1.5 A5:.5 F5:1 D5:1", "G5:1 F5:.5 E5:.5 D5:1 Bb4:1", "C#5:2 E5:2",
        # B
        "F5:.5 G5:.5 A5:1 Bb5:1 A5:1", "G5:.5 A5:.5 G5:1 E5:1 C5:1", "C5:.5 D5:.5 E5:1 A5:1.5 G5:.5",
        "F5:1 E5:.5 D5:.5 A5:2", "Bb5:1.5 A5:.5 G5:1 D5:1", "E5:1 G5:1 C6:1.5 Bb5:.5",
        "A5:1.5 F5:.5 C5:1 F5:1", "E5:2 C#5:1 E5:1",
        # C
        "C6:2 A5:1 F5:1", "G5:2 E5:1 C5:1", "D5:1 F5:1 A5:1 D6:1", "D6:1.5 C6:.5 Bb5:1 F5:1",
        "G5:1.5 Bb5:.5 D6:1 C6:.5 Bb5:.5", "A5:1 G5:1 F5:1 D5:1", "E5:1 A5:1 C#6:1 E6:1",
        "D6:.5 C#6:.5 A5:.5 G5:.5 F5:.5 E5:.5 D5:.5 C#5:.5",
    ])
    mel = parse_line(melody)
    # lead: flute doubled by violins in A/B, brass takes over in C
    mel_ab = [e for e in mel if e[0] < 64]
    mel_c = [e for e in mel if e[0] >= 64]
    mx.notes("lead", flute, mel_ab, pan=0.1, vel=0.85)
    mx.notes("lead", strings_legato, mel_ab, pan=-0.15, vel=0.55, bright=5000)
    mx.notes("lead", brass, [(b, d, m - 12) for b, d, m in mel_c], pan=0.0, vel=0.9)
    mx.notes("lead", strings_legato, mel_c, pan=-0.2, vel=0.7, bright=5500)
    mx.notes("lead", flute, [(b, d, m + 12) for b, d, m in mel_c if m + 12 <= 96], pan=0.3, vel=0.35)

    bass_ev, stacc_ev, pad_ev, harp_ev, horn_ev = [], [], [], [], []
    for bi, cname in enumerate(prog):
        b0 = bi * 4
        r, notes = chord(cname, 2)
        tones = chord(cname, 4)[1]
        # driving bass: 8ths, octave jump on the "and" of 4
        for k in range(8):
            m = r + (12 if k in (3, 7) else 0)
            bass_ev.append((b0 + k * 0.5, 0.45, m))
        # staccato strings on chord (mid register), off-beat accents
        for k in range(8):
            if bi >= 8 or k % 2 == 1:
                for m in tones[:3]:
                    stacc_ev.append((b0 + k * 0.5, 0.25, m))
        # pad / low strings sustain
        for m in chord(cname, 3)[1][:3]:
            pad_ev.append((b0, 4, m))
        # harp 16th arpeggio in B section
        if 8 <= bi < 16:
            arp = chord(cname, 5)[1][:3]
            seq = [arp[0], arp[1], arp[2], arp[1] + 12 if False else arp[0] + 12]
            for k in range(16):
                harp_ev.append((b0 + k * 0.25, 0.25, seq[k % 4] - 12))
        # horns countermelody (held 3rds) in C
        if bi >= 16:
            ht = chord(cname, 4)[1]
            horn_ev.append((b0, 2, ht[1]))
            horn_ev.append((b0 + 2, 2, ht[2] if bi % 2 else ht[0]))

    mx.notes("bass", bass, bass_ev, vel=0.9)
    mx.notes("strings", strings_stacc, stacc_ev, pan=0.35, vel=0.5)
    mx.notes("pad", strings_legato, pad_ev, pan=-0.3, vel=0.42, bright=2200)
    mx.notes("harp", pluck, harp_ev, pan=0.5, vel=0.55)
    mx.notes("horn", brass, horn_ev, pan=-0.45, vel=0.55, bright=0.6)

    # drums
    for bi in range(nbars):
        b0 = bi * 4
        for k in (0, 1.5, 2.5):
            mx.add("drums", kick(0.9), b0 + k)
        for k in (1, 3):
            mx.add("drums", snare(0.8), b0 + k, pan=0.05)
        for k in range(8):
            mx.add("drums", hat(0.7 if k % 2 else 0.45), b0 + k * 0.5, pan=-0.3)
        if bi % 8 == 7:  # fill
            for k in range(8):
                mx.add("drums", snare(0.35 + 0.08 * k), b0 + 2 + k * 0.25, pan=0.05)
        if bi % 8 == 0:
            mx.add("drums", crash(0.9), b0, pan=0.4)
        if bi % 4 == 0 or bi in (7, 15, 23):
            r = chord(prog[bi], 2)[0]
            mx.add("timp", timpani(hz(r if r >= midi_of("F2") else r + 12), 0.9), b0, pan=-0.1)
    mx.add("timp", timpani(hz(midi_of("A2")), 0.7), 23 * 4 + 3)
    mx.add("timp", timpani(hz(midi_of("A2")), 0.8), 23 * 4 + 3.5)

    stereo = render(mx, {"lead": 1.0, "bass": 0.75, "strings": 0.6, "pad": 0.55, "harp": 0.5,
                         "horn": 0.6, "drums": 0.75, "timp": 0.65},
                    wet={"lead": 0.28, "strings": 0.2, "pad": 0.35, "harp": 0.35, "horn": 0.3,
                         "drums": 0.1, "timp": 0.25, "bass": 0.03})
    loop_n = int(round(loop_s * SR))
    out = master(fold_loop(stereo, loop_n))
    export("dawnweaver_battle_normal_loop", out, loop_n, "朝霧を織る刃 (Normal Battle)")
    tracks = [("Lead", 73, 0, mel), ("Bass", 33, 1, bass_ev), ("Staccato Strings", 45, 2, stacc_ev),
              ("Pad Strings", 48, 3, pad_ev), ("Harp", 46, 4, harp_ev), ("Horns", 60, 5, horn_ev)]
    write_midi(os.path.join(OUT, "dawnweaver_battle_normal.mid"), bpm, tracks)


# =====================================================================
# 2) Boss battle  "黎明を喰らうもの"  C minor, 172 BPM, 32 bars loop
# =====================================================================
def boss_battle():
    bpm = 172
    nbars = 32
    spb = 60 / bpm
    loop_s = nbars * 4 * spb
    mx = Mix(loop_s + 4.0, bpm)

    prog = ["Cm", "Cm", "Ab", "G",
            "Cm", "Ab", "Fm", "G", "Cm", "Db", "Bb", "G",
            "Ab", "Bb", "Gm", "Cm", "Fm", "Db", "Eb", "G",
            "Cm", "Bb", "Ab", "G", "Fm", "Ab", "G", "G",
            "Cm", "Db", "Cm", "G"]
    mel_a = " ".join([
        "C5:1.5 G4:.5 C5:1 Eb5:1", "D5:1.5 Eb5:.5 C5:2", "F5:1 Eb5:.5 D5:.5 C5:1 Ab4:1", "B4:3 G4:1",
        "C5:1.5 G4:.5 C5:1 Eb5:1", "F5:1.5 Eb5:.5 Db5:2", "D5:1 F5:1 Bb5:1.5 Ab5:.5", "G5:4",
    ])
    mel_b = " ".join([
        "Eb5:1 C5:1 Ab5:2", "F5:1 D5:1 Bb5:2", "G5:1.5 F5:.5 D5:1 Bb4:1", "C5:3 Eb5:1",
        "F5:1 Ab5:1 C6:2", "Db6:1.5 C6:.5 Ab5:2", "Bb5:1 G5:1 Eb5:1 Bb5:1", "B5:2 D6:2",
    ])
    mel_c = " ".join([
        "C6:2 G5:1 Eb5:1", "D6:1.5 Bb5:.5 F5:2", "Eb6:1.5 C6:.5 Ab5:1 C6:1", "B5:2 G5:1 B5:1",
        "Ab5:1 C6:1 F6:1.5 Eb6:.5", "Eb6:1 C6:1 Ab5:1 Eb5:1", "D5:1 G5:1 B5:1 D6:1", "F6:1 Eb6:1 D6:1 B5:1",
    ])
    A = parse_line(mel_a, 16)
    B = parse_line(mel_b, 48)
    C = parse_line(mel_c, 80)
    # A: low brass melody (trombone-ish octave) + horns
    mx.notes("lead", brass, [(b, d, m - 12) for b, d, m in A], pan=-0.1, vel=0.95, bright=0.8)
    mx.notes("lead", brass, A, pan=0.15, vel=0.6, bright=0.7)
    # B: violins + flute on top, brass answer an octave down
    mx.notes("lead", strings_legato, B, pan=-0.25, vel=0.85, bright=6000)
    mx.notes("lead", strings_legato, [(b, d, m - 12) for b, d, m in B], pan=0.25, vel=0.55)
    mx.notes("lead", flute, [(b, d, m + 12) for b, d, m in B], pan=0.35, vel=0.25)
    # C: everything (climax)
    mx.notes("lead", brass, [(b, d, m - 12) for b, d, m in C], pan=0.0, vel=1.0, bright=1.0)
    mx.notes("lead", strings_legato, C, pan=-0.3, vel=0.85, bright=6500)
    mx.notes("lead", brass, [(b, d, m - 24) for b, d, m in C], pan=0.1, vel=0.6, bright=0.5)

    ost, bass_ev, hits, choir_ev, organ_ev, bell_ev = [], [], [], [], [], []
    patt = [0, 0, 7, 0, 0, 7, 12, 7]  # 3+3+2 feel in 16ths, twice per bar... (8 x 16th = 2 beats)
    for bi, cname in enumerate(prog):
        b0 = bi * 4
        r3, tones3 = chord(cname, 3)
        r2 = chord(cname, 2)[0]
        third = tones3[1] - r3
        for k in range(16):
            iv = patt[k % 8]
            if k % 8 == 6:
                iv = 12
            elif k % 8 == 4 and bi % 2:
                iv = third
            ost.append((b0 + k * 0.25, 0.2, r3 + iv))
        # bass: 3+3+2 eighth accents
        for k in (0, 1.5, 3):
            bass_ev.append((b0 + k, 0.7 if k < 3 else 0.9, r2))
        for k in (0.5, 1, 2, 2.5, 3.5):
            bass_ev.append((b0 + k, 0.3, r2))
        # brass stabs on 3+3+2 in intro / A / C
        if bi < 12 or 20 <= bi < 28:
            for k in (0, 1.5, 3):
                for m in chord(cname, 3)[1]:
                    hits.append((b0 + k, 0.45, m))
        # choir sustain from B onwards and in break
        if bi >= 12:
            for m in chord(cname, 4)[1]:
                choir_ev.append((b0, 4, m))
        # organ in break section
        if bi >= 28:
            for m in [r3 - 12] + chord(cname, 4)[1]:
                organ_ev.append((b0, 4, m))
        # ominous bell on downbeat every 2 bars in intro + break
        if (bi < 4 or bi >= 28) and bi % 2 == 0:
            bell_ev.append((b0, 2, chord(cname, 5)[0]))

    mx.notes("ost", strings_stacc, ost, pan=0.4, vel=0.6, bright=3800)
    mx.notes("ost", strings_stacc, [(b, d, m - 12) for b, d, m in ost], pan=-0.4, vel=0.45, bright=2600)
    mx.notes("bass", bass, bass_ev, vel=1.0)
    mx.notes("hits", brass, hits, pan=-0.2, vel=0.7, bright=0.9)
    mx.notes("choir", choir, choir_ev, pan=0.0, vel=0.7)
    mx.notes("organ", organ, organ_ev, pan=0.0, vel=0.8)
    mx.notes("bell", bell, bell_ev, pan=0.3, vel=0.9)

    for bi in range(nbars):
        b0 = bi * 4
        cname = prog[bi]
        intro_or_break = bi < 4 or bi >= 28
        # taiko on 3+3+2 always
        for k in (0, 1.5, 3):
            mx.add("drums", taiko(1.0 if k == 0 else 0.75), b0 + k, pan=-0.15)
        if not intro_or_break:
            for k in range(4):
                mx.add("drums", kick(0.95), b0 + k)
            for k in (1, 3):
                mx.add("drums", snare(0.9), b0 + k, pan=0.05)
            for k in range(8):
                mx.add("drums", hat(0.75 if k % 2 else 0.5, open_=(k == 7)), b0 + k * 0.5, pan=-0.35)
        if bi in (4, 12, 20):
            mx.add("drums", crash(1.0), b0, pan=0.45)
            mx.add("drums", crash(0.8), b0, pan=-0.45)
        r = chord(cname, 2)[0]
        r = r if r >= midi_of("F2") else r + 12
        mx.add("timp", timpani(hz(r), 1.0), b0)
        if bi % 4 == 3:
            for k in range(8):  # timpani roll into next phrase
                mx.add("timp", timpani(hz(r), 0.3 + 0.07 * k), b0 + 2 + k * 0.25)
    # final build into loop restart
    for k in range(16):
        mx.add("drums", snare(0.25 + 0.045 * k), 31 * 4 + k * 0.25, pan=0.05)
    mx.add("drums", swell(4 * spb, 0.9), 31 * 4, pan=0.0)

    stereo = render(mx, {"lead": 1.0, "ost": 0.55, "bass": 0.8, "hits": 0.55, "choir": 0.5,
                         "organ": 0.5, "bell": 0.45, "drums": 0.8, "timp": 0.7},
                    wet={"lead": 0.3, "ost": 0.18, "hits": 0.25, "choir": 0.45, "organ": 0.4,
                         "bell": 0.5, "drums": 0.12, "timp": 0.3, "bass": 0.03},
                    ir_decay=0.75)
    loop_n = int(round(loop_s * SR))
    out = master(fold_loop(stereo, loop_n), drive=1.7)
    export("dawnweaver_battle_boss_loop", out, loop_n, "黎明を喰らうもの (Boss Battle)")
    tracks = [("Lead", 61, 0, A + B + C), ("Ostinato", 45, 1, ost), ("Bass", 33, 2, bass_ev),
              ("Brass Hits", 61, 3, hits), ("Choir", 52, 4, choir_ev), ("Organ", 19, 5, organ_ev),
              ("Bell", 14, 6, bell_ev)]
    write_midi(os.path.join(OUT, "dawnweaver_battle_boss.mid"), bpm, tracks)


# =====================================================================
# 3) Victory  "夜明けの糸"  D major, 132 BPM, one-shot
# =====================================================================
def victory():
    bpm = 132
    spb = 60 / bpm
    total_beats = 12
    mx = Mix(total_beats * spb + 3.2, bpm)
    mel = parse_line("A4:.5 D5:.5 F#5:.5 A5:.5 G5:1 B5:1 "
                     "A5:1 E5:.5 A5:.5 C#6:1 E6:1 "
                     "D6:4")
    mx.notes("lead", brass, [(b, d, m - 12) for b, d, m in mel], pan=-0.1, vel=0.95)
    mx.notes("lead", brass, mel, pan=0.15, vel=0.65)
    mx.notes("lead", strings_legato, mel, pan=-0.3, vel=0.6, bright=6000)
    mx.notes("lead", flute, [(b, d, m + 12) for b, d, m in mel if b >= 8], pan=0.35, vel=0.3)

    harm = [(0, "D", 2), (2, "G", 2), (4, "Em", 2), (6, "A7", 2), (8, "D", 4)]
    pad_ev, bass_ev, harp_ev = [], [], []
    for b, c, d in harm:
        r, tones = chord(c, 3)
        for m in tones:
            pad_ev.append((b, d if b < 8 else 4, m))
        bass_ev.append((b, d if b < 8 else 4, chord(c, 2)[0]))
    # harp glissando up a D major scale on the final chord
    scale = [midi_of(n) for n in ["D4", "E4", "F#4", "A4", "B4", "D5", "E5", "F#5", "A5", "B5", "D6", "F#6", "A6"]]
    for i, m in enumerate(scale):
        harp_ev.append((8 + i * 0.09, 2, m))
    mx.notes("pad", strings_legato, pad_ev, pan=-0.25, vel=0.55, bright=3000)
    mx.notes("pad", brass, [(b, d, m) for b, d, m in pad_ev if b >= 8], pan=0.3, vel=0.45, bright=0.6)
    mx.notes("bass", bass, bass_ev, vel=0.8)
    mx.notes("harp", pluck, harp_ev, pan=0.45, vel=0.6, decay=0.998)
    mx.notes("bell", bell, [(8, 2, midi_of("D6")), (8.5, 2, midi_of("A6"))], pan=0.2, vel=0.6)

    mx.add("timp", timpani(hz(midi_of("D3")), 0.9), 0)
    mx.add("timp", timpani(hz(midi_of("A2")), 0.7), 6)
    for k in range(8):
        mx.add("timp", timpani(hz(midi_of("A2")), 0.3 + 0.08 * k), 6 + k * 0.25)
    mx.add("timp", timpani(hz(midi_of("D3")), 1.0), 8)
    mx.add("drums", snare(0.6), 0)
    for k in (2, 4, 6):
        mx.add("drums", kick(0.6), k)
    mx.add("drums", swell(2 * spb, 0.7), 6)
    mx.add("drums", crash(1.0), 8, pan=0.4)
    mx.add("drums", crash(0.8), 8, pan=-0.4)

    stereo = render(mx, {"lead": 1.0, "pad": 0.55, "bass": 0.6, "harp": 0.6, "bell": 0.4,
                         "timp": 0.75, "drums": 0.6},
                    wet={"lead": 0.32, "pad": 0.4, "harp": 0.4, "bell": 0.5, "timp": 0.3, "drums": 0.2})
    # one-shot: trim and fade the reverb tail
    n = int((total_beats * spb + 3.0) * SR)
    stereo = stereo[:, :n]
    fade = int(1.2 * SR)
    stereo[:, -fade:] *= np.linspace(1, 0, fade) ** 2
    out = master(stereo, drive=1.2)
    export("dawnweaver_victory_fanfare", out, None, "夜明けの糸 (Victory)")
    write_midi(os.path.join(OUT, "dawnweaver_victory_fanfare.mid"), bpm,
               [("Lead", 56, 0, mel), ("Strings", 48, 1, pad_ev), ("Bass", 33, 2, bass_ev),
                ("Harp", 46, 3, harp_ev)])


def render(mx, gains, wet, ir_decay=0.55):
    ir = make_ir(decay=ir_decay)
    total = None
    for name, b in mx.buses.items():
        g = gains.get(name, 1.0)
        w = wet.get(name, 0.0)
        sig = reverb(b * g, w, ir) if w > 0 else np.pad(b * g, ((0, 0), (0, ir.shape[1] - 1)))
        total = sig if total is None else total + sig
    return total


if __name__ == "__main__":
    import sys
    which = sys.argv[1:] or ["normal", "boss", "victory"]
    if "normal" in which:
        normal_battle()
    if "boss" in which:
        boss_battle()
    if "victory" in which:
        victory()
