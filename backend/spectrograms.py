import os
import numpy as np
import librosa
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pywt
from scipy import signal
import logging

def generate_spectrograms(file_path, selected_types, out_dir, original_basename):
    """
    Generate spectrograms for selected types only.
    
    Args:
        file_path: Path to audio file
        selected_types: List of spectrogram types to generate
        out_dir: Output directory for images
        original_basename: Original filename without extension
    
    Returns:
        dict: Generated spectrogram metadata {type: {path, name, description}}
    """
    results = {}
    
    try:
        # Load audio file
        y, sr = librosa.load(file_path, sr=None)
        logging.info(f"Loaded audio: {file_path}, sr={sr}, duration={len(y)/sr:.2f}s")
        
        # Generate only requested spectrograms
        for spec_type in selected_types:
            try:
                image_path = os.path.join(out_dir, f"{original_basename}__{spec_type}.png")
                
                if spec_type == 'mel':
                    _generate_mel_spectrogram(y, sr, image_path, original_basename)
                elif spec_type == 'cqt':
                    _generate_cqt_spectrogram(y, sr, image_path, original_basename)
                elif spec_type == 'log_stft':
                    _generate_log_stft_spectrogram(y, sr, image_path, original_basename)
                elif spec_type == 'wavelet':
                    _generate_wavelet_spectrogram(y, sr, image_path, original_basename)
                elif spec_type == 'spectral_kurtosis':
                    _generate_spectral_kurtosis(y, sr, image_path, original_basename)
                elif spec_type == 'modulation':
                    _generate_modulation_spectrogram(y, sr, image_path, original_basename)
                
                results[spec_type] = {
                    'path': image_path,
                    'name': f"{original_basename}__{spec_type}.png",
                    'description': f"{spec_type.title()} spectrogram"
                }
                
                logging.info(f"Generated {spec_type} spectrogram: {image_path}")
                
            except Exception as e:
                logging.error(f"Error generating {spec_type} spectrogram: {e}")
                continue
    
    except Exception as e:
        logging.error(f"Error loading audio file {file_path}: {e}")
    
    return results

def _generate_mel_spectrogram(y, sr, output_path, title):
    """Generate Mel-frequency spectrogram."""
    plt.figure(figsize=(12, 6))
    
    # Generate mel spectrogram
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=sr//2)
    S_db = librosa.power_to_db(S, ref=np.max)
    
    librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='mel', fmax=sr//2)
    plt.colorbar(format='%+2.0f dB')
    plt.title(f'Mel Spectrogram - {title}')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def _generate_cqt_spectrogram(y, sr, output_path, title):
    """Generate Constant-Q Transform spectrogram."""
    plt.figure(figsize=(12, 6))
    
    # Generate CQT
    C = librosa.cqt(y, sr=sr, hop_length=512, n_bins=84*2, bins_per_octave=24)
    C_db = librosa.amplitude_to_db(np.abs(C), ref=np.max)
    
    librosa.display.specshow(C_db, sr=sr, x_axis='time', y_axis='cqt_note', hop_length=512)
    plt.colorbar(format='%+2.0f dB')
    plt.title(f'Constant-Q Transform - {title}')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def _generate_log_stft_spectrogram(y, sr, output_path, title):
    """Generate Log-magnitude STFT spectrogram."""
    plt.figure(figsize=(12, 6))
    
    # Generate STFT
    D = librosa.stft(y, hop_length=512, n_fft=2048)
    S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
    
    librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='hz', hop_length=512)
    plt.colorbar(format='%+2.0f dB')
    plt.title(f'Log-magnitude STFT - {title}')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def _generate_wavelet_spectrogram(y, sr, output_path, title):
    """Generate Continuous Wavelet Transform spectrogram."""
    plt.figure(figsize=(12, 6))
    
    # Downsample for CWT if needed (CWT can be memory intensive)
    if len(y) > 100000:
        y_ds = signal.decimate(y, 4)
        sr_ds = sr // 4
    else:
        y_ds = y
        sr_ds = sr
    
    # Define scales for CWT (corresponding to frequencies)
    scales = np.logspace(1, 4, 80)  # 80 scales
    
    # Perform CWT
    coefficients, frequencies = pywt.cwt(y_ds, scales, 'morl', sampling_period=1/sr_ds)
    
    # Plot
    plt.imshow(np.abs(coefficients), aspect='auto', cmap='jet', origin='lower')
    plt.colorbar(label='Magnitude')
    plt.ylabel('Scale (Frequency)')
    plt.xlabel('Time (samples)')
    plt.title(f'Wavelet Transform - {title}')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def _generate_spectral_kurtosis(y, sr, output_path, title):
    """Generate Spectral Kurtosis representation."""
    plt.figure(figsize=(12, 6))
    
    # Compute spectrogram
    f, t, Sxx = signal.spectrogram(y, sr, window='hann', nperseg=1024, noverlap=512)
    
    # Compute spectral kurtosis along frequency axis
    # Kurtosis measures the "tailedness" of the distribution
    from scipy.stats import kurtosis
    sk = kurtosis(Sxx, axis=1, fisher=True, nan_policy='omit')
    
    # Create 2D representation by repeating SK values across time
    sk_2d = np.repeat(sk[:, np.newaxis], Sxx.shape[1], axis=1)
    
    plt.imshow(sk_2d, aspect='auto', cmap='viridis', origin='lower', extent=[t[0], t[-1], f[0], f[-1]])
    plt.colorbar(label='Spectral Kurtosis')
    plt.ylabel('Frequency (Hz)')
    plt.xlabel('Time (s)')
    plt.title(f'Spectral Kurtosis - {title}')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def _generate_modulation_spectrogram(y, sr, output_path, title):
    """Generate Modulation spectrogram."""
    plt.figure(figsize=(12, 6))
    
    # First get regular spectrogram
    f, t, Sxx = signal.spectrogram(y, sr, window='hann', nperseg=1024, noverlap=512)
    
    # Apply modulation analysis (simplified version)
    # Take log magnitude
    log_spec = np.log10(Sxx + 1e-10)
    
    # Apply 2D FFT to detect modulations
    mod_spec = np.abs(np.fft.fft2(log_spec))
    
    # Take only the first half (positive frequencies)
    mod_spec = mod_spec[:mod_spec.shape[0]//2, :mod_spec.shape[1]//2]
    
    plt.imshow(np.log10(mod_spec + 1e-10), aspect='auto', cmap='plasma', origin='lower')
    plt.colorbar(label='Log Modulation Magnitude')
    plt.ylabel('Modulation Frequency')
    plt.xlabel('Temporal Modulation')
    plt.title(f'Modulation Spectrogram - {title}')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
