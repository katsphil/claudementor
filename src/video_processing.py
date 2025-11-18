#!/usr/bin/env python3
"""
Video processing for mentoring report generation.
Transcribes video files using OpenAI Whisper API.
"""

import logging
import os
import subprocess
import shutil
from pathlib import Path
from openai import OpenAI

logger = logging.getLogger(__name__)

# Supported video/audio formats
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4a", ".mp3", ".wav"}


def get_video_duration(file_path: str) -> float:
    """Get video duration in seconds using ffprobe"""
    try:
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        raise Exception(f"Failed to get video duration: {e}")


def chunk_video(input_file: str, chunk_duration: int, output_dir: str) -> list[str]:
    """Split video into chunks using ffmpeg"""
    chunk_files = []
    duration = get_video_duration(input_file)

    logger.info(f"Video duration: {duration:.2f} seconds ({duration / 60:.2f} minutes)")

    chunk_count = int(duration / chunk_duration) + (
        1 if duration % chunk_duration > 0 else 0
    )

    if chunk_count == 1:
        logger.info(f"Extracting audio track - fits in single chunk (under {chunk_duration}s limit)")
    else:
        logger.info(f"Extracting audio track - splitting into {chunk_count} chunks of ~{chunk_duration}s each")

    for i in range(chunk_count):
        start_time = i * chunk_duration
        chunk_file = os.path.join(output_dir, f"chunk_{i:03d}.m4a")

        cmd = [
            "ffmpeg",
            "-i",
            input_file,
            "-ss",
            str(start_time),
            "-t",
            str(chunk_duration),
            "-c:a",
            "copy",  # Copy original audio codec for best quality
            "-vn",  # No video
            "-avoid_negative_ts",
            "make_zero",
            chunk_file,
            "-y",  # Overwrite output files
        ]

        logger.info(
            f"Creating chunk {i + 1}/{chunk_count}: {start_time}s - {start_time + chunk_duration}s"
        )

        try:
            subprocess.run(cmd, capture_output=True, check=True)
            chunk_files.append(chunk_file)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to create chunk {i + 1}: {e}")

    return chunk_files


def transcribe_video(filepath: str, api_key: str) -> str:
    """
    Transcribe a video file using OpenAI Whisper API.
    Returns the transcript text.
    """
    path = Path(filepath)

    # Check if file exists
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {filepath}")

    # Check file size (Whisper has a 25MB limit)
    file_size = path.stat().st_size
    max_size = 25 * 1024 * 1024  # 25MB limit
    file_size_mb = file_size / 1024 / 1024

    filename = path.name
    extension = path.suffix.lower()

    if extension not in VIDEO_EXTENSIONS:
        raise ValueError(f"Unsupported video/audio format: {extension}")

    logger.info(f"Processing video: {filename} ({file_size_mb:.1f}MB)")

    try:
        client = OpenAI(api_key=api_key)

        if file_size > max_size:
            # Large file - use chunking (extract audio in chunks)
            logger.info(
                f"Video file size: {file_size_mb:.1f}MB - will extract audio in chunks for transcription"
            )

            # Create temporary directory for chunks
            temp_base_dir = Path("working_dir/temp/video_chunks")
            temp_base_dir.mkdir(parents=True, exist_ok=True)
            temp_dir = temp_base_dir / f"video_chunks_{hash(filepath) % 10000}"
            temp_dir.mkdir(exist_ok=True)
            logger.info(f"Using temporary directory: {temp_dir}")

            try:
                # Chunk the video using ffmpeg
                chunk_duration_seconds = 900  # 15 minutes per chunk
                chunk_files = chunk_video(
                    filepath, chunk_duration_seconds, str(temp_dir)
                )

                # Transcribe each chunk
                transcripts = []
                total_chunks = len(chunk_files)

                for i, chunk_file in enumerate(chunk_files):
                    logger.info(f"Transcribing chunk {i + 1}/{total_chunks}...")
                    try:
                        with open(chunk_file, "rb") as audio_file:
                            chunk_transcript = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                response_format="text",
                            )
                        transcripts.append(chunk_transcript)

                    except Exception as e:
                        logger.warning(f"Failed to transcribe chunk {i + 1}: {e}")
                        continue

                # Combine transcripts
                transcript = "\n\n".join(transcripts)

            finally:
                # Cleanup temporary directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")

        else:
            # Small file - direct transcription (file already under 25MB limit)
            logger.info(f"File size under 25MB limit - transcribing directly")
            with open(filepath, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file, response_format="text"
                )

        logger.info(
            f"Transcription completed: {filename} ({len(transcript)} characters)"
        )

        return transcript

    except Exception as e:
        logger.error(f"Video transcription failed for {filename}: {e}")
        raise Exception(f"Video transcription failed for {filename}: {e}")


def transcribe_and_save(video_path: Path, output_dir: Path, api_key: str) -> Path:
    """
    Transcribe a video file and save transcript as .txt file.
    Returns the path to the transcript file.
    """
    try:
        # Transcribe video
        transcript = transcribe_video(str(video_path), api_key)

        # Create transcript filename
        transcript_filename = f"{video_path.stem}_transcript.txt"
        transcript_path = output_dir / transcript_filename

        # Save transcript
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(f"# Video Transcript: {video_path.name}\n\n")
            f.write(transcript)

        logger.info(f"Saved transcript: {transcript_path.name}")
        return transcript_path

    except Exception as e:
        logger.error(f"Failed to transcribe video {video_path.name}: {e}")
        raise
