import os
import librosa
import logging
from config import ALLOWED_EXTENSIONS, MAX_DURATION_SECONDS

def allowed_extension(filename):
    """Check if file extension is allowed."""
    if not filename:
        return False
    
    # Get file extension (including the dot)
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS

def get_duration_seconds(file_path):
    """Get audio file duration in seconds using librosa."""
    try:
        duration = librosa.get_duration(filename=file_path)
        return duration
    except Exception as e:
        logging.error(f"Error getting duration for {file_path}: {e}")
        return None

def validate_duration(file_path):
    """
    Validate audio file duration against MAX_DURATION_SECONDS.
    
    Returns:
        tuple: (is_valid, reason)
    """
    try:
        duration = get_duration_seconds(file_path)
        
        if duration is None:
            return False, "Could not read audio file or determine duration"
        
        if duration > MAX_DURATION_SECONDS:
            return False, f"File duration ({duration:.1f}s) exceeds maximum allowed ({MAX_DURATION_SECONDS}s)"
        
        if duration <= 0:
            return False, "Invalid audio file - duration is zero or negative"
        
        return True, None
        
    except Exception as e:
        logging.error(f"Duration validation error for {file_path}: {e}")
        return False, f"Error validating file: {str(e)}"
