"""MasterState handling.

The harness sends {"new_state": "stop"} between episodes, but Decision
only ever looked for "halt" -- so `__force_halt` was never set and the
robots kept driving through the teleport/reset between episodes.
"""

from multiprocessing import Queue

import pytest

from neonfc_ssl.core.event import Event, EventType
from neonfc_ssl.decision_layer.coaches import COACHES
from neonfc_ssl.decision_layer.decision import Decision


class _RecordingCoach:
    def __init__(self, decision):
        self.decision = decision
        self.reset_episode_calls = 0
        self.model_update_calls = 0
        self.strats = {}

    def decide(self):
        pass

    def reset_episode(self):
        self.reset_episode_calls += 1

    def model_update(self, event):
        self.model_update_calls += 1


class _CoachWithoutHooks(_RecordingCoach):
    """A coach that predates the DRL hooks entirely."""

    reset_episode = None
    model_update = None
    epsilon_greedy = None


def _decision(monkeypatch, coach_cls=_RecordingCoach, **extra_config):
    monkeypatch.setitem(COACHES, "FakeCoach", coach_cls)
    config = {"coach": "FakeCoach", "ignore_autoref": False}
    config.update(extra_config)
    decision = Decision(config, Queue())
    # In the real pipeline _start() runs inside the child process before
    # any event arrives; that's what puts the coach in place.
    decision._start()
    return decision


def _event(state):
    return Event(EventType.MASTER_STATE, "tester", "2026-01-01T00:00:00.000Z",
                 {"new_state": state})


def _halted(decision):
    return decision._Decision__force_halt


def test_stop_halts_the_robots(monkeypatch):
    decision = _decision(monkeypatch)

    decision.master_state_event(_event("stop"))

    assert _halted(decision) is True


def test_halt_still_halts(monkeypatch):
    decision = _decision(monkeypatch)

    decision.master_state_event(_event("halt"))

    assert _halted(decision) is True


def test_play_resumes_and_resets_the_episode(monkeypatch):
    decision = _decision(monkeypatch)
    decision.master_state_event(_event("stop"))

    decision.master_state_event(_event("play"))

    assert _halted(decision) is False
    assert decision._Decision__coach.reset_episode_calls == 1


def test_start_halted_is_honoured_before_any_event(monkeypatch):
    decision = _decision(monkeypatch, start_halted=True)

    assert _halted(decision) is True


def test_default_is_not_halted(monkeypatch):
    decision = _decision(monkeypatch)

    assert _halted(decision) is False


def test_coaches_without_the_hooks_are_not_fatal(monkeypatch):
    """Forwarding used to swallow every AttributeError, which hid real
    bugs; now a missing hook is simply skipped."""
    decision = _decision(monkeypatch, coach_cls=_CoachWithoutHooks)

    decision.master_state_event(_event("play"))
    decision.model_update(Event(EventType.MODEL_UPDATE, "tester",
                               "2026-01-01T00:00:00.000Z", {"models": []}))

    assert _halted(decision) is False
