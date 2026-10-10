"""Transition alignment.

a_t is sampled from s_{t-1}, so the (s, a, s') triple that gets recorded
has to be (s_{t-1}, a_{t-1}, s_t). Storing it as (s_{t-1}, a_t, s_t)
attributes the outcome to an action that hadn't happened yet, and the
learned dynamics are simply wrong.
"""

import logging

import pytest
import torch

from neonfc_ssl.decision_layer.coaches.drl_trainer import DRLCoach


class _FakeSender:
    def __init__(self):
        self.sent = []

    def send(self, payload):
        self.sent.append(payload)


class _FakeDecision:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("test-decision")
        self.strategies = set()

    def set_strategy(self, robot, strategy):
        self.strategies.add(id(robot))


def _coach(tmp_path, sender=None):
    from neonfc_ssl.decision_layer.drl.tcp_sender import TCPSender

    target = tmp_path / "striker.pt"
    net = torch.nn.Sequential(torch.nn.Linear(16, 8), torch.nn.ReLU(), torch.nn.Linear(8, 4))
    state_dict = {f"network.{k}": v for k, v in net.state_dict().items()}
    torch.save({"layer_sizes": [16, 8, 4], "state_dict": state_dict}, target)

    config = {
        "persistence_transformation": "one_v_one",
        "output_transformation": "one_v_one_output",
        "models": [
            {"id": "striker", "file_path": str(target), "transformation": "one_v_one"}
        ],
    }
    coach = DRLCoach(_FakeDecision(config))
    # Replace the real sender (if any) with one that just records.
    coach._DRLCoach__tcp = sender if sender is not None else _FakeSender()
    return coach


def _state(n):
    return torch.full((4,), float(n))


def _actions(n):
    return {"striker": torch.full((4,), float(n))}


def _propagate(coach, n):
    coach._DRLCoach__propagate(_actions(n), _state(n))


def test_only_real_transitions_are_sent(tmp_path):
    sender = _FakeSender()
    coach = _coach(tmp_path, sender)

    _propagate(coach, 0)   # s0: nothing to send yet, but cache it
    _propagate(coach, 1)   # -> (s0, a0, s1)
    _propagate(coach, 1)   # stale re-run: send nothing
    _propagate(coach, 2)   # -> (s1, a1, s2)

    assert len(sender.sent) == 2
    assert sender.sent[0] == {"cur_state": [0.0] * 4, "actions": {"striker": [0.0] * 4},
                              "next_state": [1.0] * 4}
    assert sender.sent[1] == {"cur_state": [1.0] * 4, "actions": {"striker": [1.0] * 4},
                              "next_state": [2.0] * 4}


def test_reset_episode_breaks_the_chain(tmp_path):
    sender = _FakeSender()
    coach = _coach(tmp_path, sender)

    _propagate(coach, 0)
    _propagate(coach, 1)
    coach.reset_episode()
    _propagate(coach, 3)

    assert len(sender.sent) == 1  # only the pre-reset transition


def test_cur_state_is_never_null(tmp_path):
    sender = _FakeSender()
    coach = _coach(tmp_path, sender)

    for n in range(4):
        _propagate(coach, n)

    for payload in sender.sent:
        assert payload["cur_state"] is not None
        assert payload["next_state"] is not None
