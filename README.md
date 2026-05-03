# TikTok Video Scraper

A robust and concurrent tool for downloading TikTok videos in bulk. Designed for reliability and scale, this utility utilizes asynchronous requests and yt-dlp to bypass common bot-detection mechanisms and download watermark-free videos.

## Features

- **Asynchronous Execution:** Leverages asyncio to manage concurrent download tasks efficiently.
- **Bot-Detection Bypass:** Integrates yt-dlp subprocesses to securely fetch direct video streams without triggering CAPTCHAs.
- **Automatic Retries:** Features configurable exponential backoff strategies for connection timeouts and failures.
- **Detailed Logging:** Generates comprehensive logs and structured CSV reports of failed downloads.

## Installation

1. Clone the repository or incorporate this module into your pipeline.
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure yt-dlp is installed and available in your environment:
   ```bash
   pip install yt-dlp
   ```

## Usage

Provide a list of valid TikTok video URLs in a text file (e.g., `data/urls.txt`), one per line. Execute the application with the desired arguments:

```bash
python src/downloader.py \
  --url-file data/urls.txt \
  --download-dir data/downloads \
  --batch-size 20 \
  --concurrency 5 \
  --min-delay 1.0 \
  --max-delay 3.0
```

## Configuration Parameters

- `--url-file`: Path to the input text file containing URLs.
- `--download-dir`: Target directory for saved video files.
- `--batch-size`: Number of URLs to process in a single batch.
- `--concurrency`: Maximum number of concurrent download processes.
- `--min-delay`: Minimum wait time (in seconds) between batches.
- `--max-delay`: Maximum wait time (in seconds) between batches.
- `--user-agent`: Custom User-Agent string for HTTP requests.
