"""Startup ordering: NeonFC must not die because the trainer hasn't
written its policies yet."""

import logging
import threading
import time

import pytest
import torch

from neonfc_ssl.decision_layer.coaches.drl_trainer import DRLCoach
from neonfc_ssl.decision_layer.drl.model import Model


class _FakeDecision:
    """Just enough Decision surface for DRLCoach._start()."""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("test-decision")

    def set_strategy(self, robot, strategy):
        pass


def _write_checkpoint(path):
    """A minimal checkpoint in the format Model.load expects (built with the
    real Model, so it carries every registered buffer, e.g. state_scale)."""
    model = Model([16, 8, 4], model_id="striker", epsilon=0)
    torch.save({"layer_sizes": [16, 8, 4], "state_dict": model.state_dict()}, path)


def _config(path, timeout):
    return {
        "persistence_transformation": "n_robots",
        "output_transformation": "one_v_one_output",
        "model_wait_timeout": timeout,
        "models": [{"id": "striker", "file_path": str(path), "transformation": "n_robots"}],
    }


def test_loads_once_the_file_appears(tmp_path):
    target = tmp_path / "striker.pt"

    def write_later():
        time.sleep(1.0)
        _write_checkpoint(target)

    writer = threading.Thread(target=write_later)
    writer.start()
    try:
        coach = DRLCoach(_FakeDecision(_config(target, 5.0)))
    finally:
        writer.join()

    assert "striker" in coach._DRLCoach__models


def test_raises_after_the_timeout(tmp_path):
    target = tmp_path / "never_appears.pt"
    started = time.monotonic()

    with pytest.raises(FileNotFoundError):
        DRLCoach(_FakeDecision(_config(target, 1.0)))

    assert time.monotonic() - started < 1.5


def test_zero_timeout_fails_immediately(tmp_path):
    target = tmp_path / "missing.pt"
    started = time.monotonic()

    with pytest.raises(FileNotFoundError):
        DRLCoach(_FakeDecision(_config(target, 0)))

    assert time.monotonic() - started < 0.5
