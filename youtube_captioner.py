#!/usr/bin/env python3
import argparse
import os
import tempfile
import shutil
from typing import Optional
import time
try:
    import whisper
    print("Successfully imported Whisper")
except ImportError as e:
    print(f"Error importing Whisper: {e}")
    raise
from tqdm import tqdm
import yt_dlp
from utils import validate_youtube_url, cleanup_temp_files
from srt_formatter import format_segments_to_srt

class YoutubeCaptioner:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.model = None
        print(f"Initialized temp directory at: {self.temp_dir}")
        # Check available disk space
        total, used, free = shutil.disk_usage(self.temp_dir)
        print(f"Available disk space: {free // (2**30)} GB")

    def check_ffmpeg(self):
        """Check if ffmpeg is available."""
        try:
            import subprocess
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            print("ffmpeg is available")
            return True
        except Exception as e:
            print(f"Error checking ffmpeg: {e}")
            return False

    def download_audio(self, url: str) -> Optional[str]:
        """Download audio from YouTube video."""
        if not self.check_ffmpeg():
            print("Error: ffmpeg is required but not available")
            return None

        output_template = os.path.join(self.temp_dir, "audio.%(ext)s")
        print(f"Will download audio to: {output_template}")

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'outtmpl': output_template,
            'progress_hooks': [self._download_progress_hook],
            'quiet': False,  # Enable yt-dlp's own progress output
            'verbose': True  # Add verbose output for debugging
        }

        try:
            print("Starting download with yt-dlp...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("Extracting video information...")
                info = ydl.extract_info(url, download=False)
                print(f"Video title: {info.get('title')}")
                print(f"Duration: {info.get('duration')} seconds")

                print("Starting actual download...")
                ydl.download([url])

                output_path = os.path.join(self.temp_dir, "audio.wav")
                if os.path.exists(output_path):
                    size = os.path.getsize(output_path)
                    print(f"Download completed. File size: {size // (2**20)} MB")
                    # Verify the file is not empty
                    if size == 0:
                        print("Error: Downloaded file is empty")
                        return None
                    return output_path
                else:
                    print(f"Error: Expected output file not found at {output_path}")
                    print(f"Files in temp directory: {os.listdir(self.temp_dir)}")
                    return None
        except Exception as e:
            print(f"Error downloading audio: {str(e)}")
            print(f"Current files in temp dir: {os.listdir(self.temp_dir)}")
            return None

    def _download_progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes:
                progress = (downloaded_bytes / total_bytes) * 100
                print(f"\rDownload Progress: {progress:.1f}% ({downloaded_bytes // (2**20)}MB / {total_bytes // (2**20)}MB)", end='')
        elif d['status'] == 'finished':
            print("\nDownload finished, now converting...")

    def load_model(self):
        """Load Whisper model with progress indication."""
        print("\nLoading Whisper model...")
        try:
            progress_bar = tqdm(total=100, desc="Loading model")
            print("Attempting to load base model...")

            # Try to detect CUDA availability
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Using device: {device}")

            self.model = whisper.load_model("base", device=device)
            print("Model loaded successfully")
            print(f"Model type: {type(self.model)}")
            progress_bar.update(100)
            progress_bar.close()
        except Exception as e:
            print(f"Error loading Whisper model: {str(e)}")
            raise

    def transcribe_audio(self, audio_path: str) -> Optional[list]:
        """Transcribe audio using Whisper."""
        if not self.model:
            print("Loading model since it's not loaded yet...")
            self.load_model()

        try:
            print(f"\nStarting transcription of file: {audio_path}")
            file_size = os.path.getsize(audio_path)
            print(f"File size: {file_size // (2**20)} MB")

            if file_size == 0:
                print("Error: Audio file is empty")
                return None

            print("Loading audio file into Whisper...")
            print(f"Model device: {next(self.model.parameters()).device}")

            start_time = time.time()
            result = self.model.transcribe(
                audio_path,
                verbose=True,  # Enable verbose output
                word_timestamps=True,
                language='en',  # Force English language
                task='translate',  # Translate to English if source is non-English
                beam_size=5,  # Reduce beam size for faster processing
                best_of=3,    # Reduce number of candidates for faster processing
                fp16=False    # Use FP32 for CPU processing
            )
            end_time = time.time()
            print(f"Transcription completed in {end_time - start_time:.2f} seconds")

            segments = result.get('segments', [])
            if not segments:
                print("Warning: No segments found in transcription")
                return None

            # Log first few segments to verify English output
            print("\nFirst few segments preview:")
            for i, segment in enumerate(segments[:3], 1):
                print(f"Segment {i}: {segment['text'][:100]}...")

            return segments
        except Exception as e:
            print(f"Error during transcription: {str(e)}")
            import traceback
            print("Full traceback:")
            print(traceback.format_exc())
            return None

    def generate_captions(self, url: str, output_path: str):
        """Main method to generate captions from YouTube URL."""
        if not validate_youtube_url(url):
            print("Invalid YouTube URL provided.")
            return

        try:
            # Download audio
            print(f"Starting caption generation for URL: {url}")
            audio_path = self.download_audio(url)
            if not audio_path:
                print("Failed to download audio")
                return

            # Transcribe
            print("Starting transcription process...")
            segments = self.transcribe_audio(audio_path)
            if not segments:
                print("Transcription failed")
                return

            # Generate SRT
            print("\nGenerating SRT file...")
            srt_content = format_segments_to_srt(segments)

            # Write output
            print(f"Writing output to: {output_path}")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)

            print(f"\nCaptions successfully generated: {output_path}")

        finally:
            cleanup_temp_files(self.temp_dir)

def main():
    parser = argparse.ArgumentParser(description='Generate SRT captions from YouTube videos')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('--output', '-o', default='captions.srt',
                      help='Output SRT file path (default: captions.srt)')

    args = parser.parse_args()

    captioner = YoutubeCaptioner()
    captioner.generate_captions(args.url, args.output)

if __name__ == "__main__":
    main()