import wave
import numpy as np
import os

print("--- Veritrust Strict Audio Normalization Engine ---\n")

def strict_preprocess(file_path, target_samples=48000):
    if not os.path.exists(file_path):
        print(f"[!] File not found: {file_path}")
        return None

    # [1/4] Ingest raw WAV file
    with wave.open(file_path, 'rb') as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        framerate = wav_file.getframerate()
        n_frames = wav_file.getnframes()
        raw_data = wav_file.readframes(n_frames)
        
    # Convert bytes to float array [-1.0, 1.0]
    if sample_width == 2:
        audio_signal = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
    else:
        audio_signal = np.frombuffer(raw_data, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

    # Convert stereo to mono if needed
    if channels > 1:
        audio_signal = audio_signal.reshape(-1, channels).mean(axis=1)

    print(f"[1/4] Loaded raw audio: {len(audio_signal)} samples @ {framerate}Hz")

    # [2/4] Trim Silence (Pure NumPy equivalent of librosa trim)
    # Threshold amplitude to remove leading and trailing silence
    silence_threshold = 0.02
    active_indices = np.where(np.abs(audio_signal) > silence_threshold)[0]
    
    if len(active_indices) > 0:
        audio_signal = audio_signal[active_indices[0]:active_indices[-1] + 1]
        print(f"[2/4] Trimmed silence. Active samples: {len(audio_signal)}")
    else:
        print(f"[2/4] Warning: Audio appears completely silent.")

    # [3/4] Pad or Chunk to fixed 3.0-second clips (48,000 samples)
    if len(audio_signal) > target_samples:
        # Chunk: Slice down to exactly 48,000 samples
        audio_signal = audio_signal[:target_samples]
        print(f"[3/4] Chunked audio down to exact target: {target_samples} samples")
    elif len(audio_signal) < target_samples:
        # Pad: Fill remainder with zeros (silence) to hit 48,000 samples
        padding_needed = target_samples - len(audio_signal)
        audio_signal = np.pad(audio_signal, (0, padding_needed), 'constant', constant_values=0)
        print(f"[3/4] Padded audio with zero-silence to hit: {target_samples} samples")

    # [4/4] Amplitude Normalization
    max_val = np.max(np.abs(audio_signal))
    if max_val > 0:
        audio_signal /= max_val
    
    print(f"-> Final Preprocessed Shape: {audio_signal.shape} | Peak Amplitude: {np.max(np.abs(audio_signal)):.2f}\n")
    return audio_signal

if __name__ == "__main__":
    processed_signal = strict_preprocess("data/bonafide/sample_test.wav")

