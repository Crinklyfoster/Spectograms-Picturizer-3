import numpy as np
import librosa
import logging
from scipy import stats

def extract_all_features(file_path):
    """
    Extract comprehensive audio features from file (80 features total).
    Optimized for motor fault detection and mechanical analysis.
    
    Returns:
        dict: Dictionary containing all extracted features (80 total)
    """
    try:
        # Load audio
        y, sr = librosa.load(file_path, sr=None)
        
        features = {}
        
        # Basic audio properties (6 features)
        features.update(_extract_basic_features(y, sr))
        
        # Spectral features (9 features)
        features.update(_extract_spectral_features(y, sr))
        
        # Rhythmic features (3 features)
        features.update(_extract_rhythmic_features(y, sr))
        
        # MFCC features (26 features)
        features.update(_extract_mfcc_features(y, sr))
        
        # Energy and dynamics (7 features)
        features.update(_extract_energy_features(y, sr))
        
        # NEW: Chroma features for harmonic analysis (12 features)
        features.update(_extract_chroma_features(y, sr))
        
        # NEW: Delta MFCC for capturing dynamics (13 features)
        features.update(_extract_delta_mfcc_features(y, sr))
        
        # NEW: Advanced spectral features for fault detection (4 features)
        features.update(_extract_advanced_spectral_features(y, sr))
        
        logging.info(f"Extracted {len(features)} features from {file_path}")
        return features
        
    except Exception as e:
        logging.error(f"Error extracting features from {file_path}: {e}")
        return {}

def _extract_basic_features(y, sr):
    """Extract basic audio properties (6 features)."""
    return {
        'duration': len(y) / sr,
        'sample_rate': sr,
        'total_samples': len(y),
        'channels': 1,  # librosa loads as mono by default
        'rms_energy': float(np.sqrt(np.mean(y**2))),
        'zero_crossing_rate': float(np.mean(librosa.feature.zero_crossing_rate(y)[0]))
    }

def _extract_spectral_features(y, sr):
    """Extract spectral features (9 features)."""
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
    """Extract rhythm and tempo features (3 features)."""
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
    """Extract MFCC features (26 features)."""
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    
    features = {}
    for i in range(13):
        features[f'mfcc_{i+1}_mean'] = float(np.mean(mfcc[i]))
        features[f'mfcc_{i+1}_std'] = float(np.std(mfcc[i]))
    
    return features

def _extract_energy_features(y, sr):
    """Extract energy and dynamics features (7 features)."""
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

def _extract_chroma_features(y, sr):
    """
    Extract chroma features for harmonic analysis (12 features).
    Excellent for detecting periodic faults in motors.
    """
    try:
        # Compute chromagram (pitch class profiles)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_chroma=12)
        
        features = {}
        for i in range(12):
            features[f'chroma_{i+1}'] = float(np.mean(chroma[i]))
        
        return features
        
    except Exception as e:
        logging.warning(f"Error extracting chroma features: {e}")
        # Return zeros if extraction fails
        return {f'chroma_{i+1}': 0.0 for i in range(12)}

def _extract_delta_mfcc_features(y, sr):
    """
    Extract delta MFCC features for capturing dynamics (13 features).
    Critical for motor fault detection as faults change signal dynamics.
    """
    try:
        # Compute MFCC
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        # Compute delta (first-order derivatives)
        delta_mfcc = librosa.feature.delta(mfcc, width=9, order=1)
        
        features = {}
        for i in range(13):
            features[f'delta_mfcc_{i+1}'] = float(np.mean(delta_mfcc[i]))
        
        return features
        
    except Exception as e:
        logging.warning(f"Error extracting delta MFCC features: {e}")
        return {f'delta_mfcc_{i+1}': 0.0 for i in range(13)}

def _extract_advanced_spectral_features(y, sr):
    """
    Extract advanced spectral features for fault detection (4 features).
    Specialized features for detecting mechanical anomalies.
    """
    try:
        # Compute STFT for advanced analysis
        stft = librosa.stft(y, hop_length=512, n_fft=2048)
        magnitude = np.abs(stft)
        
        # Spectral flux - measure of spectral change over time
        spectral_flux = np.mean(np.diff(magnitude, axis=1)**2)
        
        # Spectral slope - tilt of the spectrum
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        spectral_slope = []
        for frame in magnitude.T:
            if np.sum(frame) > 0:
                # Linear regression slope of log magnitude vs log frequency
                log_freqs = np.log(freqs[1:] + 1e-8)  # avoid log(0)
                log_mags = np.log(frame[1:] + 1e-8)
                slope, _, _, _, _ = stats.linregress(log_freqs, log_mags)
                spectral_slope.append(slope)
        
        # Spectral statistical moments
        flattened_spectrum = magnitude.flatten()
        spectral_skewness = float(stats.skew(flattened_spectrum))
        spectral_kurtosis_val = float(stats.kurtosis(flattened_spectrum))
        
        return {
            'spectral_flux': float(spectral_flux),
            'spectral_slope_mean': float(np.mean(spectral_slope)) if spectral_slope else 0.0,
            'spectral_skewness': spectral_skewness,
            'spectral_kurtosis_val': spectral_kurtosis_val
        }
        
    except Exception as e:
        logging.warning(f"Error extracting advanced spectral features: {e}")
        return {
            'spectral_flux': 0.0,
            'spectral_slope_mean': 0.0,
            'spectral_skewness': 0.0,
            'spectral_kurtosis_val': 0.0
        }
