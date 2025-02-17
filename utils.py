import re
import shutil
import os
from urllib.parse import urlparse, parse_qs

def validate_youtube_url(url: str) -> bool:
    """
    Validate if the provided URL is a valid YouTube URL.
    Supports various YouTube URL formats including shortened URLs.
    """
    youtube_regex = (
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    
    match = re.match(youtube_regex, url)
    if not match:
        return False
    
    return True

def get_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query)['v'][0]
    return ""

def cleanup_temp_files(temp_dir: str):
    """Clean up temporary files and directory."""
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Could not clean up temporary files: {str(e)}")

def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
