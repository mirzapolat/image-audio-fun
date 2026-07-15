# image_reverb

Wende Audio-Effekte auf Bilder an, indem das Bild als Klang interpretiert wird.
Pipeline: **Bild → WAV → Effekt → Bild**.

## Hintergrund

Ein Bild ist ein Raster aus Zahlen. Dieselben Zahlen lassen sich als
Audiosignal lesen: Wendet man darauf einen Effekt wie Reverb an und wandelt
zurück, verschmiert der Nachhall die Pixel entlang der Bildzeilen – jede Kante
zieht sichtbare Echos nach sich. Das Resultat ist ein datamosh-artiger
Glitch-Look, der sich mit klassischen Bildfiltern nicht erzeugen lässt.

Im manuellen Modus ist jeder Audioeffekt nutzbar (Reverb, Echo, Verzerrung,
EQ, …), nicht nur der eingebaute Hall.

## Installation

```
pip install numpy pillow scipy
python3 --version   # 3.8+
```

## Verwendung

### Manueller Modus (Standard)

```
python3 image_reverb.py bild.jpg
```

1. Das Skript erzeugt `bild_manual.wav` und pausiert.
2. WAV in einem Audio-Editor (z. B. Audacity) bearbeiten und **unter demselben
   Namen als WAV** speichern.
3. Im Terminal Enter drücken → Ergebnis wird als `bild_reverb.png` geschrieben.

### Automatischer Modus

Wendet den eingebauten Reverb ohne Zwischenschritt an:

```
python3 image_reverb.py bild.jpg --auto
```

## Optionen

| Option | Beschreibung |
| --- | --- |
| `-o DATEI` | Ausgabepfad (Standard: `<bild>_reverb.png`) |
| `--auto` | Eingebauten Reverb anwenden statt manueller Bearbeitung |
| `--keep-wav` | WAV-Zwischendateien behalten |
| `--delay N` | Abstand der Echos in Samples *(nur `--auto`)* |
| `--echoes N` | Anzahl der Echos *(nur `--auto`)* |
| `--decay F` | Abklingfaktor pro Echo, 0–1 *(nur `--auto`)* |
| `--wet F` | Wet/Dry-Verhältnis, 0–1 *(nur `--auto`)* |

## Hinweise

- Beim Export im Audio-Editor Samplerate und Bittiefe unverändert lassen, damit
  die Bildstruktur erhalten bleibt.
- Sehr große Bilder erzeugen entsprechend lange WAV-Dateien.

---

<sub>Danke an Hugo für die Idee.</sub>
