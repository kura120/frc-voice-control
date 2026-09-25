"""Entry point.

Usage:
    python -m voicelink --model ./vosk-model-small-en-us-0.15 --team 1234
    python -m voicelink --model ./model --server localhost   # robot simulation
    python -m voicelink --plain --model ./model --server localhost
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
from .reporting import PlainReporter


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
    ap.add_argument("--verbosity", type=int, default=config.DEFAULT_VERBOSITY, choices=(0, 1, 2))
    ap.add_argument(
        "--plain", action="store_true", help="plain scrolling text instead of the live dashboard"
    )
    ap.add_argument("--list-devices", action="store_true")
    args = ap.parse_args()
    if not args.list_devices and args.team is None and args.server is None:
        ap.error("provide --team or --server")
    return args


def make_reporter(args: argparse.Namespace):
    if args.plain:
        return PlainReporter(verbosity=args.verbosity)
    try:
        from .display import RichReporter
    except ImportError:
        print(
            "rich isn't installed (pip install rich); falling back to --plain output.",
            file=sys.stderr,
        )
        return PlainReporter(verbosity=args.verbosity)
    return RichReporter(verbosity=args.verbosity)


def run(args: argparse.Namespace, reporter) -> None:
    print("loading model...") if isinstance(reporter, PlainReporter) else None
    recognizer = Recognizer(args.model, config.SAMPLE_RATE)
    link = RobotLink(team=args.team, server=args.server)
    controller = VoiceController(link, args.min_conf, args.arm_seconds, reporter)

    ptt = None
    if not args.always_on:
        ptt = PushToTalk(parse_key(args.ptt_key), config.PTT_TAIL_SECONDS)
        ptt.start()

    audio_q: queue.Queue[bytes] = queue.Queue()

    def on_audio(indata, frames, time_info, status) -> None:
        if status:
            reporter.log(str(status))
        audio_q.put(bytes(indata))

    device = int(args.device) if args.device and args.device.isdigit() else args.device

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
                talking = args.always_on or (ptt is not None and ptt.active)
                reporter.status(connected=link.connected, listening=talking)
                controller.tick()
                try:
                    data = audio_q.get(timeout=0.1)
                except queue.Empty:
                    continue

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
            pass
        finally:
            controller.shutdown()


def main() -> None:
    args = parse_args()
    if args.list_devices:
        print(sd.query_devices())
        return

    reporter = make_reporter(args)
    with reporter:
        run(args, reporter)


if __name__ == "__main__":
    main()
