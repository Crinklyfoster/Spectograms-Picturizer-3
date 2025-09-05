import os

# Directory paths
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'

# File constraints
ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.flac', '.aac', '.m4a', '.ogg'}
MAX_DURATION_SECONDS = 600
MAX_FILES_PER_BATCH = 1048575

# Spectrogram types available
AVAILABLE_SPECTROGRAMS = [
    'mel',
    'cqt', 
    'log_stft',
    'wavelet',
    'spectral_kurtosis',
    'modulation'
]

# Default selections
DEFAULT_SPECTROGRAMS = ['mel', 'log_stft']

# Session management
SESSION_TTL_SECONDS = 3600  # 1 hour - sessions older than this can be cleaned up

def get_config():
    """Return configuration dict for templates and components."""
    return {
        'UPLOAD_FOLDER': UPLOAD_FOLDER,
        'RESULTS_FOLDER': RESULTS_FOLDER,
        'ALLOWED_EXTENSIONS': ALLOWED_EXTENSIONS,
        'MAX_DURATION_SECONDS': MAX_DURATION_SECONDS,
        'MAX_FILES_PER_BATCH': MAX_FILES_PER_BATCH,
        'AVAILABLE_SPECTROGRAMS': AVAILABLE_SPECTROGRAMS,
        'DEFAULT_SPECTROGRAMS': DEFAULT_SPECTROGRAMS,
        'SESSION_TTL_SECONDS': SESSION_TTL_SECONDS,
        'SPECTROGRAM_DESCRIPTIONS': {
            'mel': 'Mel-frequency spectrogram - emphasizes perceptually important frequencies',
            'cqt': 'Constant-Q transform - good for musical analysis with logarithmic frequency spacing',
            'log_stft': 'Log-magnitude STFT - standard time-frequency representation',
            'wavelet': 'Continuous wavelet transform - excellent for transient detection',
            'spectral_kurtosis': 'Spectral kurtosis - detects non-stationary components and faults',
            'modulation': 'Modulation spectrogram - reveals amplitude and frequency modulations'
        }
    }
