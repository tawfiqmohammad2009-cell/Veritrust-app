import wave
import numpy as np
import os

print("--- Veritrust Inference & Decision Engine ---\n")

def classify_audio(file_path, target_samples=48000, threshold=-11.0):
    if not os.path.exists(file_path):
        print(f"[!] File not found: {file_path}")
        return None

    # 1. Ingest raw WAV file
    with wave.open(file_path, 'rb') as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        n_frames = wav_file.getnframes()
        raw_data = wav_file.readframes(n_frames)
        
    # Convert bytes to float array [-1.0, 1.0]
    if sample_width == 2:
        audio_signal = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
    else:
        audio_signal = np.frombuffer(raw_data, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

    if channels > 1:
        audio_signal = audio_signal.reshape(-1, channels).mean(axis=1)

    # 2. Strict Preprocessing (Trim silence & pad/chunk to 48,000 samples)
    silence_threshold = 0.02
    active_indices = np.where(np.abs(audio_signal) > silence_threshold)[0]
    if len(active_indices) > 0:
        audio_signal = audio_signal[active_indices[0]:active_indices[-1] + 1]

    if len(audio_signal) > target_samples:
        audio_signal = audio_signal[:target_samples]
    elif len(audio_signal) < target_samples:
        audio_signal = np.pad(audio_signal, (0, target_samples - len(audio_signal)), 'constant')

    # 3. Feature Extraction
    fft_result = np.fft.rfft(audio_signal)
    power_spectrum = np.abs(fft_result) ** 2
    log_power = np.log(power_spectrum + 1e-6)
    feature_score = np.mean(log_power[:13])

    # 4. Decision Engine Logic
    print(f"-> Analyzed File: {file_path}")
    print(f"-> Extracted Feature Score: {feature_score:.4f}")
    
    # Threshold comparison
    if feature_score >= threshold:
        print("Verdict: [SECURE: Bonafide Voice] (Authentic Human)")
        return "BONAFIDE"
    else:
        print("Verdict: [ALERT: Deepfake Detected] (AI-Generated Clone)")
        return "SPOOF"

if __name__ == "__main__":
    # Test classification on our sample file
    classify_audio("data/bonafide/sample_test.wav")

