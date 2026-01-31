import whisper
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import ollama
import time

# Settings
FS = 16000  # Sample rate (Whisper prefers 16kHz)
FILENAME = "live_recording.wav"

def record_audio():
    print("\nReady! Type 'start' to begin recording.")
    cmd = input("> ").lower().strip()
    
    if cmd == "start":
        print("\n🔴 RECORDING... (Press Ctrl+C to stop)")
        audio_data = []
        
        try:
            # This captures audio until you interrupt it
            def callback(indata, frames, time, status):
                audio_data.append(indata.copy())

            with sd.InputStream(samplerate=FS, channels=1, callback=callback):
                while True:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Recording stopped.")
            
        # Save the recording
        if audio_data:
            full_audio = np.concatenate(audio_data, axis=0)
            write(FILENAME, FS, full_audio)
            return True
    return False

def process_and_summarize():
    # 1. Transcribe
    print("🧠 Transcribing...")
    model = whisper.load_model("base")

    result = model.transcribe(FILENAME, fp16=False)
    raw_text = result["text"]
    print(f"\nYou said: {raw_text}")

if __name__ == "__main__":
    if record_audio():
        process_and_summarize()