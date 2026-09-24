"""Thin wrapper around Vosk with a restricted grammar."""

import json

from vosk import KaldiRecognizer, Model, SetLogLevel

from .config import grammar


class Recognizer:
    def __init__(self, model_path: str, sample_rate: int) -> None:
        SetLogLevel(-1)
        self._rec = KaldiRecognizer(Model(model_path), sample_rate, json.dumps(grammar()))
        self._rec.SetWords(True)  # per-word confidences

    def reset(self) -> None:
        self._rec.Reset()

    def feed(self, data: bytes) -> dict | None:
        """Feed raw int16 mono audio. Returns a result dict when an utterance ends."""
        if self._rec.AcceptWaveform(data):
            return json.loads(self._rec.Result())
        return None

    def finish(self) -> dict:
        """Force out whatever has been heard so far (used on push-to-talk release)."""
        return json.loads(self._rec.FinalResult())
