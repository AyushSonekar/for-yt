from utils import format_timestamp

def format_segments_to_srt(segments: list) -> str:
    """
    Convert Whisper segments to SRT format.
    Handles proper formatting and timing of captions.
    """
    srt_content = []
    for i, segment in enumerate(segments, 1):
        # Format start and end times
        start_time = format_timestamp(segment['start'])
        end_time = format_timestamp(segment['end'])
        
        # Clean up text
        text = segment['text'].strip()
        
        # Format SRT entry
        srt_entry = (
            f"{i}\n"
            f"{start_time} --> {end_time}\n"
            f"{text}\n"
        )
        
        srt_content.append(srt_entry)
    
    return "\n".join(srt_content)
