import numpy as np
import librosa
import logging
from scipy import stats

def extract_all_features(file_path):
    """
    Extract comprehensive audio features from file.
    
    Returns:
        dict: Dictionary containing all extracted features
    """
    try:
        # Load audio
        y, sr = librosa.load(file_path, sr=None)
        
        features = {}
        
        # Basic audio properties
        features.update(_extract_basic_features(y, sr))
        
        # Spectral features
        features.update(_extract_spectral_features(y, sr))
        
        # Rhythmic features
        features.update(_extract_rhythmic_features(y, sr))
        
        # MFCC features
        features.update(_extract_mfcc_features(y, sr))
        
        # Energy and dynamics
        features.update(_extract_energy_features(y, sr))
        
        return features
        
    except Exception as e:
        logging.error(f"Error extracting features from {file_path}: {e}")
        return {}

def _extract_basic_features(y, sr):
    """Extract basic audio properties."""
    return {
        'duration': len(y) / sr,
        'sample_rate': sr,
        'total_samples': len(y),
        'channels': 1,  # librosa loads as mono by default
        'rms_energy': float(np.sqrt(np.mean(y**2))),
        'zero_crossing_rate': float(np.mean(librosa.feature.zero_crossing_rate(y)[0]))
    }

def _extract_spectral_features(y, sr):
    """Extract spectral features."""
    # Compute spectral features
    spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    
    return {
        'spectral_centroid_mean': float(np.mean(spectral_centroids)),
        'spectral_centroid_std': float(np.std(spectral_centroids)),
        'spectral_bandwidth_mean': float(np.mean(spectral_bandwidth)),
        'spectral_bandwidth_std': float(np.std(spectral_bandwidth)),
        'spectral_rolloff_mean': float(np.mean(spectral_rolloff)),
        'spectral_rolloff_std': float(np.std(spectral_rolloff)),
        'spectral_contrast_mean': float(np.mean(spectral_contrast)),
        'spectral_contrast_std': float(np.std(spectral_contrast)),
        'spectral_flatness_mean': float(np.mean(librosa.feature.spectral_flatness(y=y)[0]))
    }

def _extract_rhythmic_features(y, sr):
    """Extract rhythm and tempo features."""
    try:
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        return {
            'tempo': float(tempo),
            'beat_count': len(beats),
            'beats_per_second': len(beats) / (len(y) / sr)
        }
    except:
        return {
            'tempo': 0.0,
            'beat_count': 0,
            'beats_per_second': 0.0
        }

def _extract_mfcc_features(y, sr):
    """Extract MFCC features."""
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    
    features = {}
    for i in range(13):
        features[f'mfcc_{i+1}_mean'] = float(np.mean(mfcc[i]))
        features[f'mfcc_{i+1}_std'] = float(np.std(mfcc[i]))
    
    return features

def _extract_energy_features(y, sr):
    """Extract energy and dynamics features."""
    # RMS energy over time
    rms = librosa.feature.rms(y=y)[0]
    
    # Dynamic range
    db_values = librosa.amplitude_to_db(np.abs(y), ref=np.max)
    
    return {
        'rms_mean': float(np.mean(rms)),
        'rms_std': float(np.std(rms)),
        'dynamic_range': float(np.max(db_values) - np.min(db_values)),
        'peak_amplitude': float(np.max(np.abs(y))),
        'crest_factor': float(np.max(np.abs(y)) / np.sqrt(np.mean(y**2))),
        'db_mean': float(np.mean(db_values)),
        'db_std': float(np.std(db_values))
    }
