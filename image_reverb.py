#!/usr/bin/env python3
"""
image_reverb.py — Wende einen Reverb-(Hall-)Effekt auf ein Bild an.

Ablauf:
  1. Bild  -> Rohdaten (Pixelwerte) -> WAV
  2. WAV   -> Reverb (Faltungshall mit exponentiell abfallendem Impuls)
  3. WAV   -> zurueck in ein Bild

Der Reverb verschmiert die Pixelwerte entlang der Zeilen und erzeugt so
sichtbare "Echos" / Nachhall im Bild.

Benutzung:
    # Standard = manueller Modus: WAV wird erzeugt, du bearbeitest sie selbst
    # (z. B. in Audacity), Enter -> zurueck ins Bild
    python3 image_reverb.py input.jpg

    # Automatischer Modus: eingebauter Reverb, ohne Warten
    python3 image_reverb.py input.jpg --auto
    python3 image_reverb.py input.jpg --auto -o output.png --decay 0.4 --wet 0.6

    python3 image_reverb.py input.jpg --keep-wav   # WAV-Zwischendateien behalten
"""

import argparse
import os
import numpy as np
from PIL import Image
from scipy.io import wavfile

SAMPLE_RATE = 44100  # nur fuer die WAV-Metadaten; hat keinen Einfluss auf das Bild


# --------------------------------------------------------------------------- #
#  1. Bild  ->  Audio                                                         #
# --------------------------------------------------------------------------- #
def image_to_audio(path):
    """Laedt ein Bild und wandelt es in ein Float-Audiosignal in [-1, 1] um.

    Rueckgabe: (samples, meta) — meta merkt sich Form/Modus zum Rekonstruieren.
    """
    img = Image.open(path)
    mode = img.mode
    if mode not in ("L", "RGB", "RGBA"):
        img = img.convert("RGB")
        mode = "RGB"

    arr = np.asarray(img)                      # (H, W) oder (H, W, C), uint8
    meta = {"shape": arr.shape, "mode": mode}

    # Pixel 0..255  ->  Audio -1..1
    flat = arr.astype(np.float32).ravel()
    samples = (flat / 127.5) - 1.0
    return samples, meta


# --------------------------------------------------------------------------- #
#  2. Reverb                                                                  #
# --------------------------------------------------------------------------- #
def make_impulse_response(delay, num_echoes, decay):
    """Baut eine einfache Impulsantwort: eine Reihe abklingender Echos."""
    length = delay * num_echoes + 1
    ir = np.zeros(length, dtype=np.float32)
    ir[0] = 1.0                                # Direktschall
    for k in range(1, num_echoes + 1):
        idx = k * delay
        if idx < length:
            ir[idx] = decay ** k               # jedes Echo leiser
    return ir


def apply_reverb(samples, delay, num_echoes, decay, wet):
    """Faltet das Signal mit der Impulsantwort (Reverb) und mischt wet/dry."""
    ir = make_impulse_response(delay, num_echoes, decay)
    wet_sig = np.convolve(samples, ir, mode="full")[: len(samples)]

    # Normieren, damit es nicht uebersteuert
    peak = np.max(np.abs(wet_sig))
    if peak > 0:
        wet_sig = wet_sig / peak

    out = (1.0 - wet) * samples + wet * wet_sig
    return out.astype(np.float32)


# --------------------------------------------------------------------------- #
#  3. Audio  ->  Bild                                                         #
# --------------------------------------------------------------------------- #
def audio_to_image(samples, meta):
    """Wandelt das Audiosignal zurueck in ein Bild derselben Form."""
    shape = meta["shape"]
    n = int(np.prod(shape))

    sig = samples[:n]
    if len(sig) < n:                           # Reverb kann laenger sein -> auffuellen
        sig = np.pad(sig, (0, n - len(sig)))

    # Audio -1..1  ->  Pixel 0..255
    pixels = (sig + 1.0) * 127.5
    pixels = np.clip(pixels, 0, 255).astype(np.uint8)
    arr = pixels.reshape(shape)
    return Image.fromarray(arr, mode=meta["mode"])


# --------------------------------------------------------------------------- #
#  Main                                                                       #
# --------------------------------------------------------------------------- #
def main():
    p = argparse.ArgumentParser(description="Reverb-Effekt auf ein Bild anwenden.")
    p.add_argument("input", help="Eingabebild (jpg, png, ...)")
    p.add_argument("-o", "--output", help="Ausgabebild (Standard: <input>_reverb.png)")
    p.add_argument("--delay", type=int, default=70,
                   help="Abstand zwischen Echos in Samples/Pixeln (Standard: 70)")
    p.add_argument("--echoes", type=int, default=20,
                   help="Anzahl der Echos (Standard: 20)")
    p.add_argument("--decay", type=float, default=0.75,
                   help="Abklingfaktor pro Echo, 0..1 (Standard: 0.75)")
    p.add_argument("--wet", type=float, default=0.75,
                   help="Anteil des Halls im Mix, 0..1 (Standard: 0.75)")
    p.add_argument("--keep-wav", action="store_true",
                   help="WAV-Zwischendateien behalten")
    p.add_argument("--auto", action="store_true",
                   help="Automatischer Modus: eingebauten Reverb anwenden, "
                        "ohne auf manuelle Bearbeitung zu warten")
    args = p.parse_args()

    base = os.path.splitext(args.input)[0]
    output = args.output or base + "_reverb.png"
    wav_dry = base + "_dry.wav"
    wav_wet = base + "_wet.wav"

    # Standard: manueller Modus. Nur mit --auto laeuft der eingebaute Reverb.
    if not args.auto:
        manual_mode(args.input, output, base + "_manual.wav", args.keep_wav)
        return

    print(f"[1/3] Bild -> Audio: {args.input}")
    samples, meta = image_to_audio(args.input)
    wavfile.write(wav_dry, SAMPLE_RATE, samples)
    print(f"      {meta['mode']} {meta['shape']}  ->  {len(samples)} Samples")

    print(f"[2/3] Reverb (delay={args.delay}, echoes={args.echoes}, "
          f"decay={args.decay}, wet={args.wet})")
    reverbed = apply_reverb(samples, args.delay, args.echoes, args.decay, args.wet)
    wavfile.write(wav_wet, SAMPLE_RATE, reverbed)

    print(f"[3/3] Audio -> Bild: {output}")
    result = audio_to_image(reverbed, meta)
    result.save(output)

    if not args.keep_wav:
        os.remove(wav_dry)
        os.remove(wav_wet)
    else:
        print(f"      WAVs behalten: {wav_dry}, {wav_wet}")

    print("Fertig.")


def manual_mode(input_path, output, wav_path, keep_wav):
    """Erzeugt die WAV, wartet auf den Nutzer, wandelt sie dann zurueck ins Bild."""
    print(f"[1/2] Bild -> Audio: {input_path}")
    samples, meta = image_to_audio(input_path)
    wavfile.write(wav_path, SAMPLE_RATE, samples)
    print(f"      {meta['mode']} {meta['shape']}  ->  {len(samples)} Samples")
    print()
    print(f"  WAV erzeugt: {wav_path}")
    print("  Bearbeite die Datei jetzt nach Belieben (z. B. in Audacity) und")
    print("  SPEICHERE sie unter demselben Namen als Mono-WAV.")
    print("  Hinweis: Laenge und Samplerate sind egal - das Bild wird auf die")
    print("  Originalgroesse zugeschnitten/aufgefuellt.")
    print()
    input("  >> Enter druecken, wenn du fertig bist ...")

    print(f"\n[2/2] Audio -> Bild: {output}")
    data = wavfile.read(wav_path)[1]
    edited = wav_data_to_float(data)
    result = audio_to_image(edited, meta)
    result.save(output)

    if not keep_wav:
        os.remove(wav_path)
    else:
        print(f"      WAV behalten: {wav_path}")

    print("Fertig.")


def wav_data_to_float(data):
    """Normalisiert gelesene WAV-Daten (beliebiger dtype/Kanaele) nach [-1, 1].

    scipy liefert je nach WAV-Format int16/int32/uint8 oder float32.
    """
    if data.ndim > 1:                          # Stereo -> Mono (Mittelwert)
        data = data.mean(axis=1)
    dt = data.dtype

    if dt == np.uint8:                         # 8-bit PCM ist unsigned (0..255)
        return (data.astype(np.float32) - 128.0) / 128.0
    if np.issubdtype(dt, np.integer):          # 16-/32-bit signed PCM
        return data.astype(np.float32) / np.iinfo(dt).max
    # bereits Float
    return data.astype(np.float32)


if __name__ == "__main__":
    main()
