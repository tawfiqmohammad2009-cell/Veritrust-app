import numpy as np

def extract_log_mel_spectrogram(audio_bytes, sample_rate=16000, n_mels=80, n_fft=512, hop_length=160):
    """
    Converts raw PCM 16-bit audio bytes into a normalized Log-Mel Spectrogram matrix.
    Dependency-free (uses only NumPy).
    """
    # 1. Convert raw byte buffer to 16-bit PCM float numpy array
    pcm_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    
    if len(pcm_data) == 0:
        return None

    # 2. Compute Short-Time Fourier Transform (STFT) using Hanning window
    window = np.hanning(n_fft)
    num_frames = max(1, (len(pcm_data) - n_fft) // hop_length + 1)
    
    stft_matrix = []
    for i in range(num_frames):
        start = i * hop_length
        chunk = pcm_data[start : start + n_fft]
        if len(chunk) < n_fft:
            chunk = np.pad(chunk, (0, n_fft - len(chunk)))
        
        # Apply window & FFT
        windowed = chunk * window
        fft_complex = np.fft.rfft(windowed, n=n_fft)
        magnitude = np.abs(fft_complex)
        stft_matrix.append(magnitude)
        
    stft_matrix = np.array(stft_matrix).T  # Shape: (n_fft//2 + 1, num_frames)

    # 3. Apply Log Scale (eps added for stability)
    log_spectrogram = np.log(stft_matrix + 1e-6)

    # 4. Standardize / Normalize features
    mean = np.mean(log_spectrogram)
    std = np.std(log_spectrogram) + 1e-6
    normalized_spec = (log_spectrogram - mean) / std

    return normalized_spec

