import whisper
import sys

model = whisper.load_model('small')
result = model.transcribe(sys.argv[1], language='zh')
print(result['text'])
