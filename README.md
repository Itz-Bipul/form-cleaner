# 📝 FormCleaner – Keep Only Black Text

[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://formcleaner.streamlit.app)   <!-- replace with your deployed app link -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A **Streamlit web application** that strips all colours from scanned forms and PDFs, preserving only **black text**.  
Ideal for cleaning documents before printing, OCR processing, or archival.

---

## 📋 Table of Contents
- [Description](#-description)
- [Features](#-features)
- [Demo](#-demo)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Configuration](#-configuration)
- [Build & Test](#-build--test)
- [Dependencies](#-dependencies)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)
- [Acknowledgments](#-acknowledgments)

---

## 📖 Description

**FormCleaner** solves a common problem: scanned forms often contain coloured backgrounds, guidelines, logos, or watermarks that interfere with further processing.  
This tool:

- Converts all non‑black pixels to white (or transparent).
- Uses a simple **grayscale threshold** – you control how “black” is considered text.
- Handles both **images** (JPG, PNG, TIFF, BMP) and **multi‑page PDFs**.
- Provides a **real‑time web interface** for instant preview and download.

The core filtering logic is a single function (`keep_only_black`) that can be reused in your own Python scripts or pipelines.

---

## ✨ Features

| Feature | Details |
|--------|---------|
| 🖼️ **Image Support** | PNG, JPG, JPEG, TIFF, BMP |
| 📄 **PDF Support** | Multi‑page PDF → filtered pages → new PDF or ZIP of images |
| 🎚️ **Adjustable Threshold** | Slider to fine‑tune “blackness” detection (0‑255) |
| 🔲 **Transparent Background** | Export PNGs with transparent background (not for PDF) |
| 📥 **Multiple Output Formats** | Download as clean image (PNG/JPEG), PDF, or ZIP of pages |
| ⚡ **Real‑time Preview** | See changes instantly before downloading |
| 📱 **Responsive UI** | Works on desktop and mobile browsers |

---

## 🎬 Demo

![FormCleaner Demo](screenshots/demo.gif)   <!-- replace with your GIF/video -->

*Live demo available at: [https://formcleaner.streamlit.app](https://formcleaner.streamlit.app)* (to be deployed)

---

## 🔧 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/Itz-Bipul/form-cleaner.git
   cd form-cleaner