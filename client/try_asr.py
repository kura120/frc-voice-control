import queue

import sounddevice as sd

from voicelink.asr import Recognizer
from voicelink.config import SAMPLE_RATE

rec = Recognizer("./model", SAMPLE_RATE)
q = queue.Queue()
sd.RawInputStream(
    samplerate=SAMPLE_RATE,
    blocksize=1600,
    dtype="int16",
    channels=1,
    callback=lambda d, f, t, s: q.put(bytes(d)),
).start()
print("speak your vocabulary, Ctrl+C to quit")
while True:
    result = rec.feed(q.get())
    if result and result.get("text"):
        print(result)
