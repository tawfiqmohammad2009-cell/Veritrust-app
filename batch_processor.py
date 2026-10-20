import os
import wave
import numpy as np

print("--- Veritrust Batch Dataset Processor ---\n")

def extract_features(file_path):
    with wave.open(file_path, 'rb') as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        n_frames = wav_file.getnframes()
        raw_data = wav_file.readframes(n_frames)
        
    if sample_width == 2:
        audio_signal = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
    else:
        audio_signal = np.frombuffer(raw_data, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

    if channels > 1:
        audio_signal = audio_signal.reshape(-1, channels).mean(axis=1)

    # Spectral feature extraction proxy
    fft_result = np.fft.rfft(audio_signal)
    power_spectrum = np.abs(fft_result) ** 2
    log_power = np.log(power_spectrum + 1e-6)
    return np.mean(log_power[:13])

def process_directory(base_dir, label):
    if not os.path.exists(base_dir):
        print(f"[!] Directory not found: {base_dir}")
        return
    
    files = [f for f in os.listdir(base_dir) if f.endswith('.wav')]
    print(f"Scanning [{base_dir}] -> Found {len(files)} audio files.")
    
    for file_name in files:
        file_path = os.path.join(base_dir, file_name)
        feature = extract_features(file_path)
        print(f"   -> File: {file_name} | Label: {label} | Feature Score: {feature:.4f}")

if __name__ == "__main__":
    process_directory("data/bonafide", label="BONAFIDE (Real)")
    process_directory("data/spoof", label="SPOOF (AI-Generated)")
    print("\nBatch scanning routine ready!")

