"""Entry point.

    python -m voicelink --model ./vosk-model-small-en-us-0.15 --team 1234
    python -m voicelink --model ./model --server localhost   # robot simulation
    python -m voicelink --list-devices
"""

import argparse
import queue
import sys

import sounddevice as sd

from . import config
from .asr import Recognizer
from .controller import VoiceController
from .link import RobotLink
from .ptt import PushToTalk, parse_key


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="voicelink", description="FRC voice command bridge")
    ap.add_argument("--model", default="model", help="path to Vosk model folder")
    target = ap.add_mutually_exclusive_group()
    target.add_argument("--team", type=int, help="FRC team number")
    target.add_argument("--server", help="NT server host/IP (localhost for sim, 10.TE.AM.2)")
    ap.add_argument("--device", help="input device index or name substring")
    ap.add_argument("--ptt-key", default=config.DEFAULT_PTT_KEY)
    ap.add_argument("--always-on", action="store_true", help="skip push-to-talk (not recommended)")
    ap.add_argument("--min-conf", type=float, default=config.DEFAULT_MIN_CONF)
    ap.add_argument("--arm-seconds", type=float, default=config.DEFAULT_ARM_SECONDS)
    ap.add_argument("--list-devices", action="store_true")
    args = ap.parse_args()
    if not args.list_devices and args.team is None and args.server is None:
        ap.error("provide --team or --server")
    return args


def main() -> None:
    args = parse_args()
    if args.list_devices:
        print(sd.query_devices())
        return

    print("loading model...")
    recognizer = Recognizer(args.model, config.SAMPLE_RATE)
    controller = VoiceController(
        RobotLink(team=args.team, server=args.server), args.min_conf, args.arm_seconds
    )

    ptt = None
    if not args.always_on:
        ptt = PushToTalk(parse_key(args.ptt_key), config.PTT_TAIL_SECONDS)
        ptt.start()

    audio_q: queue.Queue[bytes] = queue.Queue()

    def on_audio(indata, frames, time_info, status) -> None:
        if status:
            print(status, file=sys.stderr)
        audio_q.put(bytes(indata))

    device = int(args.device) if args.device and args.device.isdigit() else args.device
    mode = "always listening" if ptt is None else f"hold [{args.ptt_key}] to talk"
    print(f"ready: {mode}. Say '{config.ARM_PHRASE}' then a command. Ctrl+C to quit.")

    was_talking = False
    with sd.RawInputStream(
        samplerate=config.SAMPLE_RATE,
        blocksize=config.BLOCK_SIZE,
        device=device,
        dtype="int16",
        channels=1,
        callback=on_audio,
    ):
        try:
            while True:
                controller.tick()
                try:
                    data = audio_q.get(timeout=0.1)
                except queue.Empty:
                    continue

                talking = ptt is None or ptt.active
                if talking:
                    if not was_talking:
                        recognizer.reset()
                    result = recognizer.feed(data)
                    if result:
                        controller.handle(result)
                elif was_talking:
                    controller.handle(recognizer.finish())
                was_talking = talking
        except KeyboardInterrupt:
            print("\nbye")
        finally:
            controller.shutdown()


if __name__ == "__main__":
    main()
