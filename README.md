git clone https://github.com/yourusername/youtube-caption-generator.git
cd youtube-caption-generator
pip install flask flask-wtf openai-whisper yt-dlp tqdm torch

# Install FFmpeg
# Ubuntu/Debian
sudo apt-get install ffmpeg
# macOS
brew install ffmpeg
# Windows: Download from https://www.ffmpeg.org/download.html
```

## Usage

1. Start the server:
```bash
python app.py