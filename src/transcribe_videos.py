#!/usr/bin/env python3
"""
Batch video transcription using Moonshine (ONNX).

Processes all .mp4 files in the downloads directory, extracts audio,
transcribes using Moonshine via the moonshine_onnx package, and saves
results as JSON.

Usage:
    conda run -n ai-agent python transcribe_videos.py
    conda run -n ai-agent python transcribe_videos.py --input-dir /path/to/videos
    conda run -n ai-agent python transcribe_videos.py --models-dir ./models/moonshine-tiny
"""

import os
import sys
import json
import argparse
import subprocess
import tempfile
import logging
import time
from pathlib import Path

import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(str(Path(__file__).resolve().parent.parent.parent / "tiktokdownload.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
SAMPLE_RATE = 16_000
MAX_SEGMENT_SEC = 60          # Moonshine supports up to 64s; use 60 for safety
OVERLAP_SEC = 1               # 1s overlap between chunks to avoid cutting words


def extract_audio(video_path: Path, output_wav: Path) -> bool:
    """Extract mono 16 kHz WAV audio from a video file using FFmpeg."""
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn",                     # no video
        "-acodec", "pcm_s16le",    # 16-bit PCM
        "-ar", str(SAMPLE_RATE),   # 16 kHz
        "-ac", "1",                # mono
        str(output_wav),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"FFmpeg failed for {video_path.name}: {result.stderr[-300:]}")
        return False
    return True


def load_audio_numpy(wav_path: Path) -> np.ndarray:
    """Load a WAV file as a float32 numpy array."""
    import soundfile as sf
    audio, sr = sf.read(str(wav_path), dtype="float32")
    if sr != SAMPLE_RATE:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=SAMPLE_RATE)
    return audio


def chunk_audio(audio: np.ndarray, max_sec: int = MAX_SEGMENT_SEC,
                overlap_sec: int = OVERLAP_SEC) -> list:
    """
    Split audio into chunks of max_sec with overlap.
    Returns list of (chunk_array, start_time_seconds).
    """
    max_samples = max_sec * SAMPLE_RATE
    overlap_samples = overlap_sec * SAMPLE_RATE
    step = max_samples - overlap_samples

    if len(audio) <= max_samples:
        return [(audio, 0.0)]

    chunks = []
    start = 0
    while start < len(audio):
        end = min(start + max_samples, len(audio))
        chunk = audio[start:end]
        # Skip very short trailing chunks (< 0.5s)
        if len(chunk) < SAMPLE_RATE // 2:
            break
        chunks.append((chunk, start / SAMPLE_RATE))
        start += step

    return chunks


def transcribe_audio(audio: np.ndarray, model, tokenizer) -> str:
    """
    Transcribe a numpy audio array using Moonshine ONNX.
    Handles chunking for audio longer than 60s.
    """
    chunks = chunk_audio(audio)
    all_texts = []

    for i, (chunk, start_time) in enumerate(chunks):
        # moonshine_onnx expects shape [1, num_samples]
        audio_input = chunk[np.newaxis, :]

        tokens = model.generate(audio_input)
        text = tokenizer.decode_batch(tokens)[0].strip()

        if text:
            all_texts.append(text)

        if len(chunks) > 1:
            logger.info(f"  Chunk {i+1}/{len(chunks)} ({start_time:.1f}s): {text[:80]}...")

    full_text = " ".join(all_texts)
    return full_text


def main():
    parser = argparse.ArgumentParser(description="Transcribe videos using Moonshine Base")
    parser.add_argument(
        "--input-dir",
        default=str(Path(__file__).parent / "data" / "downloads"),
        help="Directory containing .mp4 files",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for JSON transcripts (default: <input-dir>/transcripts)",
    )
    parser.add_argument(
        "--models-dir",
        default=str(Path(__file__).parent / "models" / "moonshine-base"),
        help="Local directory containing encoder_model.onnx and decoder_model_merged.onnx",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip videos that already have transcripts",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir) if args.output_dir else input_dir / "transcripts"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all MP4 files
    videos = sorted(input_dir.glob("*.mp4"))
    if not videos:
        logger.error(f"No .mp4 files found in {input_dir}")
        sys.exit(1)

    logger.info(f"Found {len(videos)} videos in {input_dir}")

    # ── Load model ─────────────────────────────────────────────────────────────
    from moonshine_onnx import MoonshineOnnxModel, load_tokenizer

    models_dir = Path(args.models_dir)
    logger.info(f"Loading Moonshine model from: {models_dir}")

    # Determine model size from directory name for layer config
    if "tiny" in models_dir.name:
        model_name = "moonshine/tiny"
    else:
        model_name = "moonshine/base"

    model = MoonshineOnnxModel(models_dir=str(models_dir), model_name=model_name)
    tokenizer = load_tokenizer()

    logger.info("Model loaded successfully!")

    # ── Process each video ─────────────────────────────────────────────────────
    results_summary = []
    total_start = time.time()

    for idx, video_path in enumerate(videos, 1):
        video_id = video_path.stem
        output_file = output_dir / f"{video_id}.json"

        # Skip if already transcribed
        if args.skip_existing and output_file.exists():
            logger.info(f"[{idx}/{len(videos)}] Skipping {video_id} (already transcribed)")
            continue

        logger.info(f"[{idx}/{len(videos)}] Processing: {video_path.name}")
        vid_start = time.time()

        # Extract audio to a temp WAV file
        with tempfile.TemporaryDirectory(dir=input_dir) as tmpdir:
            wav_path = Path(tmpdir) / f"{video_id}.wav"

            if not extract_audio(video_path, wav_path):
                logger.error(f"  Failed to extract audio from {video_path.name}")
                results_summary.append({"video": video_path.name, "status": "FAILED", "error": "ffmpeg"})
                continue

            # Load audio
            audio = load_audio_numpy(wav_path)
            duration = len(audio) / SAMPLE_RATE
            logger.info(f"  Audio duration: {duration:.1f}s")

            if duration < 0.1:
                logger.warning(f"  Audio too short ({duration:.2f}s), skipping")
                results_summary.append({"video": video_path.name, "status": "SKIPPED", "error": "too_short"})
                continue

        # Transcribe
        text = transcribe_audio(audio, model, tokenizer)
        elapsed = time.time() - vid_start

        # Save result
        result = {
            "video_file": video_path.name,
            "video_id": video_id,
            "duration_seconds": round(duration, 2),
            "transcription_time_seconds": round(elapsed, 2),
            "text": text,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"  Transcript: {text[:120]}...")
        logger.info(f"  Done in {elapsed:.1f}s → {output_file.name}")
        results_summary.append({"video": video_path.name, "status": "OK", "text_len": len(text), "time": round(elapsed, 2)})

    # ── Summary ────────────────────────────────────────────────────────────────
    total_elapsed = time.time() - total_start
    summary_file = output_dir / "_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_videos": len(videos),
            "total_time_seconds": round(total_elapsed, 2),
            "results": results_summary,
        }, f, ensure_ascii=False, indent=2)

    ok_count = sum(1 for r in results_summary if r["status"] == "OK")
    logger.info(f"\nDone! Transcribed {ok_count}/{len(videos)} videos in {total_elapsed:.1f}s.")
    logger.info(f"Results saved to: {output_dir}")


if __name__ == "__main__":
    main()
