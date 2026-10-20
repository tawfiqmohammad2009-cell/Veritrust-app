import wave
import numpy as np
import os

print("--- Veritrust Real Audio Ingestion Module ---\n")

def load_real_wav(file_path):
    if not os.path.exists(file_path):
        print(f"[!] File not found: {file_path}")
        print("-> Please place a sample .wav file in this directory to test.")
        return None

    with wave.open(file_path, 'rb') as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        framerate = wav_file.getframerate()
        n_frames = wav_file.getnframes()
        
        print(f"[1/3] Reading WAV Metadata:")
        print(f"    - Channels: {channels}")
        print(f"    - Sample Width: {sample_width} bytes")
        print(f"    - Sample Rate: {framerate} Hz")
        print(f"    - Total Frames: {n_frames}")
        
        # Read raw audio bytes
        raw_data = wav_file.readframes(n_frames)
        
    # Convert bytes to numpy array based on sample width
    if sample_width == 2:
        audio_signal = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)
        # Normalize 16-bit integer audio to range [-1.0, 1.0]
        audio_signal /= 32768.0
    else:
        audio_signal = np.frombuffer(raw_data, dtype=np.uint8).astype(np.float32)
        audio_signal = (audio_signal - 128) / 128.0

    print(f"[2/3] Converted {len(audio_signal)} samples to floating-point array.")
    
    # Handle stereo to mono conversion if necessary
    if channels > 1:
        audio_signal = audio_signal.reshape(-1, channels).mean(axis=1)
        print(f"[3/3] Converted stereo to mono. Final shape: {audio_signal.shape}")
    else:
        print(f"[3/3] Audio is already mono.")

    return audio_signal, framerate

if __name__ == "__main__":
    # You can change 'sample_test.wav' to any real .wav file on your device
    signal, sr = load_real_wav("sample_test.wav")
    if signal is not None:
        print("\nReal Audio Ingestion Pipeline Verified Successfully!")

