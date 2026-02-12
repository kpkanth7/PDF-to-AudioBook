"""
PDF → Audiobook (cross-platform)

Why this approach:
- PyPDF2: extracts text from PDFs (works on all OSes).
- pyttsx3: offline text-to-speech that works on Windows/macOS/Linux.
- tkinter file picker: lets user select a PDF without typing paths (more user-friendly).

Important notes:
- Some PDFs are scanned images. PyPDF2 can’t "read" images → you'd need OCR for those.
- Saving audio with pyttsx3 is not perfectly consistent across all OS engines.
  Chunking the text and saving multiple files is the most reliable universal approach.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, List, Tuple
import shutil
import subprocess

import pyttsx3
from PyPDF2 import PdfReader

from tkinter import Tk
from tkinter.filedialog import askopenfilename


# ----------------------------
# 1) Small data container for settings
# ----------------------------
@dataclass
class TTSSettings:
    voice_id: Optional[str]
    rate: int
    mode: str  # "S" speak, "R" record, "B" both
    save_format: str  # "wav" by default, optionally "mp3" if ffmpeg is present you'll need to download it for your system. 


# ----------------------------
# 2) File picker (user doesn't type paths)
# ----------------------------
def pick_pdf_file() -> Optional[Path]:
    """
    Opens the OS-native file picker and returns selected PDF path. Remember Only PDF's 
    We hide the Tk window because we only want the dialog.
    """
    root = Tk()
    root.withdraw()
    root.update()
    file_path = askopenfilename(
        title="Select a PDF file",
        filetypes=[("PDF files", "*.pdf")],
    )
    root.destroy()

    if not file_path:
        return None
    return Path(file_path).expanduser().resolve()


# ----------------------------
# 3) PDF text extraction
# ----------------------------
def extract_pdf_text(pdf_path: Path) -> str:
    """
    Extracts text from all pages using PyPDF2.
    If a PDF is scanned/image-only, extract_text() may return empty -> OCR needed.
    """
    reader = PdfReader(str(pdf_path))
    if not reader.pages:
        return ""

    parts: List[str] = []
    total = len(reader.pages)

    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        print(f"Page {i}/{total} chars={len(text)}")
        if text:
            parts.append(text)

    return "\n".join(parts).strip()


# ----------------------------
# 4) Chunking (reliability)
# ----------------------------
def chunk_text(text: str, max_chars: int = 1200) -> Iterable[str]:
    """
    We chunk the text because:
    - Some TTS engines struggle with very long strings.
    - Saving to file is more reliable in chunks across platforms.
    """
    text = " ".join(text.split())  # normalize whitespace
    for i in range(0, len(text), max_chars):
        yield text[i : i + max_chars]


# ----------------------------
# 5) Voice selection
# ----------------------------
def list_voices(engine: pyttsx3.Engine) -> List[Tuple[int, str, str]]:
    """
    Returns list of (index, display_name, voice_id). 175 of them so choose what suits you the best.
    voice_id is what we pass into engine.setProperty("voice", voice_id)
    """
    voices = engine.getProperty("voices") or []
    items: List[Tuple[int, str, str]] = []

    for idx, v in enumerate(voices):
        name = getattr(v, "name", "") or "Unknown"
        vid = getattr(v, "id", "") or ""
        items.append((idx, name, vid))

    return items


def choose_voice(engine: pyttsx3.Engine) -> Optional[str]:
    """
    Prompts user to choose a voice by number. If you're fine with anything just hit enter
    Enter = default voice.
    """
    items = list_voices(engine)
    if not items:
        print("No voices found. Using default voice.")
        return None

    print("\nAvailable voices:")
    for idx, name, _ in items:
        print(f"  [{idx}] {name}")

    while True:
        s = input("\nChoose a voice number (Enter for default): ").strip()
        if s == "":
            return None
        if s.isdigit():
            i = int(s)
            if 0 <= i < len(items):
                return items[i][2]
        print("Invalid choice. Try again.")


# ----------------------------
# 6) Rate + Mode + Format selection
# ----------------------------
def choose_rate(default_rate: int = 170) -> int:
    """
    Rate affects speaking speed. Go higher for Faster output. 
    """
    while True:
        s = input(f"Choose speed/rate (default {default_rate}, higher=faster): ").strip()
        if s == "":
            return default_rate
        if s.isdigit():
            r = int(s)
            if 80 <= r <= 350:
                return r
        print("Invalid rate. Enter a number between 80 and 350 (or press Enter).")


def choose_mode() -> str:
    """
    Speak vs Record vs Both.
    """
    print("\nMode options:")
    print("  S = Speak only (no saving)")
    print("  R = Record only (save audio, no speaking)")
    print("  B = Both (speak + save)")
    while True:
        m = input("Choose mode [S/R/B] (default S): ").strip().upper()
        if m == "":
            return "S"
        if m in {"S", "R", "B"}:
            return m
        print("Invalid mode. Choose S, R, or B.")


def has_ffmpeg() -> bool:
    """
    ffmpeg is the easiest universal converter for mp3/m4a.
    We detect it so we can offer mp3 output optionally.
    """
    return shutil.which("ffmpeg") is not None


def choose_save_format() -> str:
    """
    WAV is universal, but large.
    MP3 is smaller, but needs ffmpeg.
    """
    if not has_ffmpeg():
        return "wav"

    print("\nSave format options:")
    print("  wav = Universal, but bigger files")
    print("  mp3 = Smaller files (requires ffmpeg, detected ✅)")
    while True:
        s = input("Choose save format [wav/mp3] (default wav): ").strip().lower()
        if s == "":
            return "wav"
        if s in {"wav", "mp3"}:
            return s
        print("Invalid choice. Choose wav or mp3.")


def collect_settings(engine: pyttsx3.Engine) -> TTSSettings:
    """
    Collect all settings BEFORE starting playback,
    so the user doesn't get interrupted mid-audio.
    """
    voice_id = choose_voice(engine)
    rate = choose_rate()
    mode = choose_mode()

    # Only ask about save format if user is recording
    save_format = "wav"
    if mode in {"R", "B"}:
        save_format = choose_save_format()

    return TTSSettings(voice_id=voice_id, rate=rate, mode=mode, save_format=save_format)


# ----------------------------
# 7) Speak and/or Save
# ----------------------------
def configure_engine(engine: pyttsx3.Engine, settings: TTSSettings) -> None:
    """
    Apply voice + rate to engine once.
    """
    engine.setProperty("rate", settings.rate)
    engine.setProperty("volume", 1.0)
    if settings.voice_id:
        engine.setProperty("voice", settings.voice_id)


def save_wav_chunks(engine: pyttsx3.Engine, text: str, base_name: str, out_dir: Path) -> List[Path]:
    """
    Save audio in multiple WAV chunk files:
      base_name_part001.wav, base_name_part002.wav, ...
    Chunking increases cross-platform reliability for pyttsx3 save_to_file().
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    files: List[Path] = []

    for idx, part in enumerate(chunk_text(text), start=1):
        p = out_dir / f"{base_name}_part{idx:03d}.wav"
        files.append(p)
        engine.save_to_file(part, str(p))

    return files


def convert_wav_to_mp3(wav_file: Path) -> Path:
    """
    Convert one wav to mp3 using ffmpeg.
    Only used if ffmpeg is installed and user chose mp3.
    """
    mp3_file = wav_file.with_suffix(".mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_file), str(mp3_file)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return mp3_file


def speak_text(engine: pyttsx3.Engine, text: str) -> None:
    """
    Speak the text in chunks to avoid giant strings.
    """
    for part in chunk_text(text):
        engine.say(part)
    engine.runAndWait()


# ----------------------------
# 8) Main
# ----------------------------
def main():
    pdf_path = pick_pdf_file()
    if not pdf_path:
        raise SystemExit("No PDF selected. Exiting.")

    print("Selected:", pdf_path)

    text = extract_pdf_text(pdf_path)
    if not text:
        raise SystemExit(
            "No extractable text found in this PDF.\n"
            "If it's a scanned PDF (image-only), you'll need OCR first."
        )

    print("TOTAL chars:", len(text))

    engine = pyttsx3.init()
    settings = collect_settings(engine)
    configure_engine(engine, settings)

    base_name = pdf_path.stem
    out_dir = Path.cwd() / "output_audio"

    # Record (optional)
    saved_files: List[Path] = []
    # RECORD
    if settings.mode in {"R", "B"}:
        print("\nRecording enabled… (saving WAV chunks)")
        record_engine = pyttsx3.init()
        configure_engine(record_engine, settings)

        wav_files = save_wav_chunks(record_engine, text, base_name, out_dir)
        record_engine.runAndWait()  # run saving queue

        if settings.save_format == "mp3":
            print("Converting to MP3 (ffmpeg)…")
            saved_files = [convert_wav_to_mp3(w) for w in wav_files]
        else:
            saved_files = wav_files

    # SPEAK (use a fresh engine if we also recorded, Because I encountered an eror while Using B it was only recording not speaking so I decided to split it.)
    if settings.mode in {"S", "B"}:
        print("\nSpeaking…")
        speak_engine = pyttsx3.init()
        configure_engine(speak_engine, settings)

        speak_text(speak_engine, text)  # speak_text already does runAndWait()


    # Print saved output
    if saved_files:
        print(f"\nSaved {len(saved_files)} file(s) in: {out_dir}")
        for f in saved_files[:10]:
            print(" -", f.name)
        if len(saved_files) > 10:
            print(" ...")


if __name__ == "__main__":
    main()
