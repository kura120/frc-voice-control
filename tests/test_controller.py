from unittest.mock import patch

from voicelink.controller import VoiceController


class FakeLink:
    def __init__(self):
        self.sent = []
        self.armed_states = []

    def send(self, command):
        self.sent.append(command)
        return True

    def set_armed(self, armed):
        self.armed_states.append(armed)


def heard(text, conf=0.9):
    return {"text": text, "result": [{"word": w, "conf": conf} for w in text.split()]}


def make(min_conf=0.6, arm_seconds=8.0):
    link = FakeLink()
    return VoiceController(link, min_conf, arm_seconds), link


def test_command_ignored_when_not_armed():
    ctrl, link = make()
    ctrl.handle(heard("shoot"))
    assert link.sent == []


def test_command_sent_after_arm():
    ctrl, link = make()
    ctrl.handle(heard("activate"))
    ctrl.handle(heard("shoot"))
    assert link.sent == ["SHOOT"]
    assert link.armed_states == [True]


def test_multiword_command_maps_to_id():
    ctrl, link = make()
    ctrl.handle(heard("activate"))
    ctrl.handle(heard("auto one"))
    assert link.sent == ["AUTO_1"]


def test_stop_works_without_arming():
    ctrl, link = make()
    ctrl.handle(heard("stop"))
    assert link.sent == ["STOP"]


def test_disarm_blocks_further_commands():
    ctrl, link = make()
    ctrl.handle(heard("activate"))
    ctrl.handle(heard("deactivate"))
    ctrl.handle(heard("shoot"))
    assert link.sent == []
    assert link.armed_states == [True, False]


def test_low_confidence_is_rejected():
    ctrl, link = make(min_conf=0.6)
    ctrl.handle(heard("activate"))
    ctrl.handle(heard("shoot", conf=0.3))
    assert link.sent == []


def test_unknown_word_is_rejected():
    ctrl, link = make()
    ctrl.handle(heard("activate"))
    ctrl.handle(heard("shoot [unk]"))
    assert link.sent == []


def test_empty_and_unmapped_text_do_nothing():
    ctrl, link = make()
    ctrl.handle({"text": ""})
    ctrl.handle(heard("activate"))
    ctrl.handle(heard("banana"))
    assert link.sent == []


def test_arming_expires():
    now = [100.0]
    with patch("voicelink.controller.time.monotonic", lambda: now[0]):
        ctrl, link = make(arm_seconds=8.0)
        ctrl.handle(heard("activate"))
        now[0] += 7.9
        ctrl.handle(heard("shoot"))
        now[0] += 0.2
        ctrl.handle(heard("intake"))
        ctrl.tick()
    assert link.sent == ["SHOOT"]
    assert link.armed_states == [True, False]


def test_shutdown_disarms():
    ctrl, link = make()
    ctrl.handle(heard("activate"))
    ctrl.shutdown()
    assert link.armed_states[-1] is False
    assert not ctrl.armed
