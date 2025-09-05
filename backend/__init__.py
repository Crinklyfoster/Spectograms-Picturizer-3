"""
Audio Processor v3.0 Backend Package

This package contains the core audio processing functionality:
- Spectrogram generation (spectrograms.py)
- Feature extraction (features.py)
- Utility functions (utils.py)
"""

# Import main functions for easier access
from .spectrograms import generate_spectrograms
from .features import extract_all_features
from .utils import (
    save_uploaded_files,
    get_upload_path,
    create_zip_for_spectrograms,
    clear_session
)

# Package metadata
__version__ = "3.0.0"
__author__ = "Audio Processor Team"
__description__ = "Backend processing functions for audio analysis"

# Available spectrogram types (imported from config but defined here for reference)
SUPPORTED_SPECTROGRAMS = [
    'mel',
    'cqt', 
    'log_stft',
    'wavelet',
    'spectral_kurtosis',
    'modulation'
]

# Export main functions
__all__ = [
    'generate_spectrograms',
    'extract_all_features',
    'save_uploaded_files',
    'get_upload_path',
    'create_zip_for_spectrograms',
    'clear_session',
    'SUPPORTED_SPECTROGRAMS'
]
