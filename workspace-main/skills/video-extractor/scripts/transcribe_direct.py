"""Direct whisper transcription test with medium model."""
import sys
import os

# Force UTF-8 output
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

import whisper

audio_path = sys.argv[1]
model = whisper.load_model("medium")
result = model.transcribe(audio_path, language="zh")
print(result["text"])
