# AI TikTok Categorization Pipeline

A high-performance, fully automated pipeline for downloading TikTok videos at scale, transcribing them using state-of-the-art offline AI, and visualizing the results through a real-time, glassmorphic web dashboard.

---

## 🚀 Features

- **Concurrent Downloader**: Uses `asyncio` and `yt-dlp` to bypass TikTok protections. Supports batch processing, exponential backoff, and robust error logging.
- **Offline AI Transcription**: Powered by **Moonshine (ONNX)**. Processes video audio locally using CPU-optimized `base` or `tiny` models. Includes automatic 60s audio chunking to bypass model context limits.
- **Modern Web Dashboard**: A sleek, dark-mode Flask web interface featuring glassmorphism, live log streaming, and synchronized video/transcript viewing.
- **Idempotent Execution**: All scripts are designed to resume where they left off (skipping existing downloads and existing transcripts).

---

## 📁 Repository Structure

```text
.
├── src/
│   ├── download_tiktok_videos.py  # Asynchronous bulk video downloader
│   ├── transcribe_videos.py       # Moonshine STT transcription engine
│   └── app.py                     # Flask-based web dashboard
├── data/
│   ├── urls.txt                   # Input file: one TikTok URL per line
│   └── downloads/                 # Downloaded .mp4 videos
│       └── transcripts/           # Generated .json transcripts
├── models/                        # Local Moonshine ONNX model weights
│   ├── moonshine-base/            # High-accuracy model (default)
│   └── moonshine-tiny/            # High-speed model
├── tiktokdownload.log             # Unified system logs
└── requirements.txt               # Python dependencies
```

---

## 🛠️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/harb993/tik-transcrip.git
   cd tik-transcrip
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install System Dependencies (FFmpeg)**:
   FFmpeg is required by the transcription script to extract 16kHz mono audio from the MP4 files.
   ```bash
   sudo apt update && sudo apt install ffmpeg -y
   ```

---

## 📖 Component Details & Usage

The pipeline consists of three distinct stages. You can run them sequentially or concurrently.

### 1. The Downloader (`src/download_tiktok_videos.py`)
This script reads URLs from a text file and downloads them concurrently. It wraps `yt-dlp` in `asyncio` subprocesses to avoid API blocks and CAPTCHAs. Failed downloads are saved to `failed_urls.csv` for easy retrying.

**Basic Usage:**
```bash
python src/download_tiktok_videos.py
```

**Advanced Configuration (CLI Arguments):**
- `--url-file`: Path to input URLs (default: `data/urls.txt`)
- `--download-dir`: Output directory (default: `data/downloads`)
- `--batch-size`: Concurrent tasks per chunk (default: `50`)
- `--concurrency`: Max simultaneous HTTP requests (default: `20`)
- `--min-delay`: Min seconds to sleep between batches (default: `2.0`)
- `--max-delay`: Max seconds to sleep between batches (default: `5.0`)
- `--user-agent`: Override the default browser user-agent.

### 2. The AI Transcriber (`src/transcribe_videos.py`)
This script iterates over all `.mp4` files in the download directory. It uses `ffmpeg` to extract the audio, processes it using the local Moonshine ONNX model, and saves a structured JSON file containing the transcribed text and execution metrics. Audio longer than 60 seconds is automatically chunked with a 1-second overlap.

**Basic Usage:**
```bash
python src/transcribe_videos.py
```

**Advanced Configuration (CLI Arguments):**
- `--input-dir`: Directory containing MP4s (default: `data/downloads`)
- `--output-dir`: Output for JSONs (default: `data/downloads/transcripts`)
- `--models-dir`: Path to the local ONNX models (default: `models/moonshine-base`)
- `--skip-existing`: Skips videos that already have a JSON transcript (default: `True`)

*Note: If you are running on low-end hardware, you can switch to the tiny model by passing `--models-dir ./models/moonshine-tiny`.*

### 3. The Web Dashboard (`src/app.py`)
A lightweight Flask server that provides a gorgeous frontend to review your dataset. It reads directly from your local filesystem and streams the `tiktokdownload.log` file live.

**Basic Usage:**
```bash
python src/app.py
```
After running, open your browser and navigate to: **http://localhost:5002**

**Dashboard Features:**
- **Video Queue**: Left sidebar showing all downloaded MP4s with their transcript processing status (Pending/Ready).
- **Visual Feed**: Embedded HTML5 video player that autoplays upon selection.
- **AI Transcript**: Displays the extracted text or notifies you if the video contains no speech/music only.
- **System Logs**: Live-updating terminal window tracking the backend Python logs.

---

## 📝 License
MIT License
