from faster_whisper import WhisperModel
import sounddevice as sd
import scipy.io.wavfile as wav
import tempfile

# Load FastWhisper
WHISPER_MODEL = WhisperModel("base", compute_type="int8")

def record_and_transcribe(duration=5, sample_rate=16000):
    print(f"Recording for {duration} seconds...")

    # Record audio
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()

    # Save to temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav.write(f.name, sample_rate, recording)
        audio_path = f.name

    # Transcribe
    segments, _ = WHISPER_MODEL.transcribe(audio_path, language="en")
    text = "".join([segment.text for segment in segments])
    print(f"Transcribed: {text.strip()}")
    return text.strip()