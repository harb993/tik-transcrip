# TikTok Categorization Pipeline

A high-performance, concurrent pipeline for downloading TikTok videos, transcribing them with AI, and visualizing results through a real-time dashboard.

##  Features

- **Concurrent Downloader**: Uses `asyncio` and `yt-dlp` for high-speed, watermark-free video downloads.
- **AI Transcription**: Powered by **Moonshine (ONNX)** for lightning-fast, CPU-optimized Speech-to-Text.
- **Matrix Dashboard**: A real-time Flask-based web interface to monitor logs, watch videos, and read transcripts.
- **Robust Pipeline**: Includes automatic retries, exponential backoff, and detailed logging.

##  Repository Structure

```text
.
├── src/
│   ├── download_tiktok_videos.py  # Primary downloader script
│   ├── transcribe_videos.py       # Moonshine STT transcription script
│   └── app.py                     # Flask Dashboard
├── data/
│   ├── urls.txt                   # Input URLs list
│   └── downloads/                 # Downloaded videos (.mp4)
│       └── transcripts/           # Generated transcripts (.json)
├── models/                        # Local Moonshine ONNX models
└── requirements.txt               # Dependencies
```

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/harb993/Categorization_pipeline.git
   cd Categorization_pipeline
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **External Dependencies**:
   Ensure `ffmpeg` is installed on your system for audio extraction:
   ```bash
   sudo apt update && sudo apt install ffmpeg
   ```

## Usage

### 1. Download Videos
Add your TikTok URLs to `data/urls.txt` (one per line) and run:
```bash
python src/download_tiktok_videos.py
```

### 2. Transcribe Videos
Process the downloaded videos to extract text using Moonshine:
```bash
python src/transcribe_videos.py
```

### 3. Launch Dashboard
Visualize your pipeline and results in real-time:
```bash
python src/app.py
```
Then open `http://localhost:5002` in your browser.

##  Configuration

- **Transcription**: The system uses `moonshine/base` by default (stored in `models/`). You can switch to `moonshine/tiny` for even faster performance on low-end hardware.
- **Concurrency**: Adjust download speed in `src/download_tiktok_videos.py` by modifying the `--concurrency` argument.

##  License
MIT
