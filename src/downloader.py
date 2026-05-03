#!/usr/bin/env python3
import os
import sys
import argparse
import random
import asyncio
import aiohttp
import logging
import pandas as pd
from tqdm import tqdm
import re
from pathlib import Path

# SETUP LOGGING
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("tiktokdownload.log"),
        logging.StreamHandler()
    ]
)


async def download_video(session, url, download_dir, headers, max_retries=3):
    video_id = url.rstrip("/").split("/")[-1]
    file_path = download_dir / f"{video_id}.mp4"
    if file_path.exists():
        logging.info(f"Video {video_id} already exists, skipping.")
        return None

    backoff = 1
    for attempt in range(1, max_retries + 1):
        try:
            # Use yt-dlp sequentially as an asyncio subprocess to bypass TikTok bot protections
            yt_dlp_executable = sys.executable.replace("python", "yt-dlp")
            yt_dlp_cmd = [
                yt_dlp_executable,
                "--quiet",
                "--no-warnings",
                "--no-check-certificate",
                "-o", str(download_dir / f"{video_id}.%(ext)s"),
                url
            ]
            
            process = await asyncio.create_subprocess_exec(
                *yt_dlp_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logging.info(f"Downloaded: {file_path}")
                return None
            else:
                err_msg = stderr.decode().strip()
                raise Exception(f"yt-dlp failed: {err_msg}")

        except Exception as e:
            if attempt < max_retries:
                logging.warning(
                    f"Attempt {attempt} failed for {url} ({e}), "
                    f"retrying in {backoff}s..."
                )
                await asyncio.sleep(backoff)
                backoff *= 2
                continue
            else:
                logging.error(
                    f"All {max_retries} attempts failed for {url}: {e}"
                )
                return url


async def process_batch(session, batch, sem, download_dir, headers):
    failed = []

    async def bounded_download(u):
        async with sem:
            return await download_video(session, u, download_dir, headers)

    tasks = [bounded_download(u) for u in batch]
    for coro in tqdm(
        asyncio.as_completed(tasks),
        total=len(tasks),
        desc="Downloading videos"
    ):
        result = await coro
        if result:
            failed.append(result)
    return failed


async def main(args):
    url_file = Path(args.url_file)
    download_dir = Path(args.download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    video_urls = [
        u.strip() for u in url_file.read_text().splitlines() if u.strip()
    ]
    total = len(video_urls)
    logging.info(f"Processing {total} URLs from {url_file}")

    headers = {
        "User-Agent": args.user_agent,
        "Referer": "https://www.tiktok.com/"
    }
    sem = asyncio.Semaphore(args.concurrency)
    all_failed = []

    async with aiohttp.ClientSession() as session:
        for i in range(0, total, args.batch_size):
            batch = video_urls[i: i + args.batch_size]
            idx = i // args.batch_size + 1
            total_batches = (
                total + args.batch_size - 1
            ) // args.batch_size
            logging.info(f"Processing batch {idx} of {total_batches}")

            failed = await process_batch(
                session, batch, sem, download_dir, headers
            )
            all_failed.extend(failed)

            Path("failed_urls.txt").write_text(
                "\n".join(all_failed)
            )
            logging.info(
                f"Completed batch {idx}. Total failed: "
                f"{len(all_failed)}"
            )

            await asyncio.sleep(
                random.uniform(args.min_delay, args.max_delay)
            )

    df = pd.DataFrame({"Failed URLs": all_failed})
    df.to_csv("failed_urls.csv", index=False)
    logging.info(
        "Download completed. Reports written to failed_urls.txt / .csv"
    )


# CLI ENTRYPOINT
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bulk TikTok Video Downloader"
    )
    parser.add_argument(
        "--url-file",
        default=os.environ.get("URL_FILE", "urls.txt"),
        help="Path to text file with one TikTok URL per line"
    )
    parser.add_argument(
        "--download-dir",
        default=os.environ.get("DOWNLOAD_DIR", "downloaded_videos"),
        help="Directory to save downloaded MP4s"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.environ.get("BATCH_SIZE", 50)),
        help="Number of concurrent tasks per batch"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=int(os.environ.get("CONCURRENCY", 20)),
        help="Max simultaneous HTTP requests"
    )
    parser.add_argument(
        "--min-delay",
        type=float,
        default=float(os.environ.get("MIN_DELAY", 2)),
        help="Minimum delay (s) between batches"
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=float(os.environ.get("MAX_DELAY", 5)),
        help="Maximum delay (s) between batches"
    )
    parser.add_argument(
        "--user-agent",
        default=os.environ.get(
            "USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        ),
        help="User-Agent string to use for HTTP requests"
    )

    args = parser.parse_args()

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        logging.warning("Script interrupted by user. Exiting.")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)
