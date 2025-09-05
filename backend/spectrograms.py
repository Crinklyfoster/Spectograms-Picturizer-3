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
    Uses v2.0 algorithms and styling for superior visual quality.
    
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
        # Load audio file (same as v2.0)
        y, sr = librosa.load(file_path, sr=None)
        logging.info(f"Loaded audio: {file_path}, sr={sr}, duration={len(y)/sr:.2f}s")
        
        # Generate only requested spectrograms
        for spec_type in selected_types:
            try:
                image_path = os.path.join(out_dir, f"{original_basename}__{spec_type}.png")
                
                if spec_type == 'mel':
                    _generate_mel_spectrogram(y, sr, image_path)
                elif spec_type == 'cqt':
                    _generate_cqt_spectrogram(y, sr, image_path)
                elif spec_type == 'log_stft':
                    _generate_log_stft_spectrogram(y, sr, image_path)
                elif spec_type == 'wavelet':
                    _generate_wavelet_scalogram(y, sr, image_path)
                elif spec_type == 'spectral_kurtosis':
                    _generate_spectral_kurtosis(y, sr, image_path)
                elif spec_type == 'modulation':
                    _generate_modulation_spectrogram(y, sr, image_path)
                
                # Verify the file was created
                if os.path.exists(image_path):
                    results[spec_type] = {
                        'path': image_path,
                        'name': f"{original_basename}__{spec_type}.png",
                        'description': f"{spec_type.title()} spectrogram"
                    }
                    logging.info(f"Successfully generated {spec_type} spectrogram: {image_path}")
                else:
                    logging.error(f"Failed to create {spec_type} spectrogram file: {image_path}")
                
            except Exception as e:
                logging.error(f"Error generating {spec_type} spectrogram: {e}", exc_info=True)
                continue
    
    except Exception as e:
        logging.error(f"Error loading audio file {file_path}: {e}", exc_info=True)
        raise
    
    return results

def _generate_mel_spectrogram(y, sr, save_path):
    """Generate Mel-Spectrogram (exact v2.0 implementation)."""
    plt.figure(figsize=(12, 8))
    mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=sr//2)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    librosa.display.specshow(mel_spec_db, sr=sr, x_axis='time', y_axis='mel', fmax=sr//2)
    plt.colorbar(format='%+2.0f dB')
    plt.title('Mel-Spectrogram\n(Energy imbalance, tonal shifts, soft degradation patterns)', fontsize=14)
    plt.xlabel('Time (s)')
    plt.ylabel('Mel Frequency')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

def _generate_cqt_spectrogram(y, sr, save_path):
    """Generate CQT (exact v2.0 implementation)."""
    plt.figure(figsize=(12, 8))
    cqt = librosa.cqt(y, sr=sr, hop_length=512, n_bins=84)  # v2.0 uses n_bins=84, not 84*2
    cqt_db = librosa.amplitude_to_db(np.abs(cqt), ref=np.max)
    librosa.display.specshow(cqt_db, sr=sr, x_axis='time', y_axis='cqt_note')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Constant-Q Transform (CQT)\n(Harmonic noise, shifted frequency content)', fontsize=14)
    plt.xlabel('Time (s)')
    plt.ylabel('CQT Frequency')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

def _generate_log_stft_spectrogram(y, sr, save_path):
    """Generate Log-STFT (exact v2.0 implementation)."""
    plt.figure(figsize=(12, 8))
    stft = librosa.stft(y, hop_length=512, n_fft=2048)
    stft_db = librosa.amplitude_to_db(np.abs(stft), ref=np.max)
    librosa.display.specshow(stft_db, sr=sr, x_axis='time', y_axis='log')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Log-STFT Spectrogram\n(Low-frequency rumble, imbalance, looseness)', fontsize=14)
    plt.xlabel('Time (s)')
    plt.ylabel('Log Frequency (Hz)')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

def _generate_wavelet_scalogram(y, sr, save_path):
    """Generate Wavelet Scalogram (exact v2.0 implementation)."""
    plt.figure(figsize=(12, 8))
    
    # Exact v2.0 resampling logic
    if len(y) > 50000:
        y_resampled = signal.resample(y, 50000)
    else:
        y_resampled = y
    
    # Exact v2.0 parameters
    scales = np.arange(1, 128)
    coefficients, frequencies = pywt.cwt(y_resampled, scales, 'morl', sampling_period=1/sr)
    
    # Exact v2.0 plotting
    plt.imshow(np.abs(coefficients), extent=[0, len(y_resampled)/sr, frequencies[-1], frequencies[0]],
               cmap='hot', aspect='auto', interpolation='bilinear')
    plt.colorbar(label='Magnitude')
    plt.title('Wavelet Scalogram\n(Short bursts, transient spikes from loose components)', fontsize=14)
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

def _generate_spectral_kurtosis(y, sr, save_path):
    """Generate Spectral Kurtosis (exact v2.0 implementation)."""
    plt.figure(figsize=(12, 8))
    
    # Exact v2.0 algorithm
    f, t, stft = signal.spectrogram(y, sr, nperseg=2048, noverlap=1024)
    stft_magnitude = np.abs(stft)
    spectral_kurtosis = np.zeros_like(stft_magnitude)
    
    for i in range(stft_magnitude.shape[0]):
        freq_data = stft_magnitude[i, :]
        if np.std(freq_data) > 0:
            mean_val = np.mean(freq_data)
            std_val = np.std(freq_data)
            kurtosis_val = np.mean(((freq_data - mean_val) / std_val) ** 4) - 3
            spectral_kurtosis[i, :] = kurtosis_val
    
    # Exact v2.0 plotting
    plt.imshow(spectral_kurtosis, extent=[t[0], t[-1], f[0], f[-1]],
               cmap='viridis', aspect='auto', origin='lower')
    plt.colorbar(label='Kurtosis')
    plt.title('Spectral Kurtosis\n(Impulses and sudden power shifts)', fontsize=14)
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

def _generate_modulation_spectrogram(y, sr, save_path):
    """Generate Modulation Spectrogram (exact v2.0 implementation)."""
    plt.figure(figsize=(12, 8))
    
    # Exact v2.0 algorithm
    analytic_signal = signal.hilbert(y)
    envelope = np.abs(analytic_signal)
    f, t, envelope_spec = signal.spectrogram(envelope, sr, nperseg=2048, noverlap=1024)
    envelope_spec_db = 10 * np.log10(envelope_spec + 1e-10)
    
    # Exact v2.0 plotting
    plt.imshow(envelope_spec_db, extent=[t[0], t[-1], f[0], f[-1]],
               cmap='plasma', aspect='auto', origin='lower')
    plt.colorbar(label='Power (dB)')
    plt.title('Modulation Spectrogram\n(Wobble or sideband-type modulation from winding faults)', fontsize=14)
    plt.xlabel('Time (s)')
    plt.ylabel('Modulation Frequency (Hz)')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
