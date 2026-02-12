# 📖 PDF to Audiobook (Cross-Platform)

A simple, cross-platform Python tool that converts **text-based PDFs into spoken audio** or **audiobook files**, with user-friendly customization.

This project allows you to:
- Select a PDF using a **file picker** (no paths required)
- Choose **voice** and **speech speed** before playback
- Decide whether to:
  - 🔊 Speak the PDF out loud
  - 💾 Save the PDF as audio files
  - 🔊💾 Do both
- Optionally convert saved audio into **MP3** for easy sharing

The goal is to make PDFs more **accessible**, **listenable**, and **portable**, without relying on cloud services.

---

## 🎯 Project Motivation

Reading long PDFs (resumes, research papers, notes, books) can be tiring or inaccessible in many situations.  
This project was built to:

- Turn PDFs into **audio-first content**
- Keep everything **offline & privacy-friendly**
- Work **universally** across macOS, Windows, and Linux
- Stay beginner-friendly and easy to extend

---

## ⚙️ Features

- Cross-platform **offline Text-to-Speech**
- Native **file picker** (no command-line paths)
- Voice and speed selection **before playback**
- Optional audio saving (WAV by default)
- Optional MP3 conversion (if `ffmpeg` is installed)
- Handles large PDFs safely using text chunking

---
## ⚠️ Limitations & 🚀 Future Improvements

- Works only for text-based PDFs
- Scanned/image PDFs require OCR (not included)
- Audio files may be large if PDFs are long
- Have to build OCR fallback for scanned PDFs
- Have to Merge audio chunks into a single file
- In the Future Can Implement Chapter Based Audio Splitting


## 🧰 Prerequisites

### Required
- Python **3.9+**
- pip

### Python Libraries
```bash
pip install pyttsx3 PyPDF2
