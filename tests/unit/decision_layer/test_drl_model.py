"""Stochastic play on the serving side.

Acting on tanh(mean) with epsilon=0 gave the agent no exploration at all,
and a per-frame uniform target just averages out in the P-controller.
"""

import torch

from neonfc_ssl.decision_layer.drl.model import Model
from neonfc_ssl.decision_layer.drl.model_event import ModelReference


def _checkpoint(path, log_std=None):
    net = torch.nn.Sequential(
        torch.nn.Linear(16, 8), torch.nn.ReLU(), torch.nn.Linear(8, 4)
    )
    state_dict = {f"network.{k}": v for k, v in net.state_dict().items()}
    payload = {"layer_sizes": [16, 8, 4], "state_dict": state_dict}
    if log_std is not None:
        payload["log_std"] = log_std
    torch.save(payload, path)
    return path


def test_checkpoint_without_log_std_is_deterministic(tmp_path):
    model = Model.load(_checkpoint(tmp_path / "m.pt"), "striker")
    model.stochastic = True

    state = torch.randn(16)
    assert model.log_std is None
    with torch.no_grad():
        expected = torch.tanh(model.network(state.float()))

    assert torch.allclose(model.inference(state), expected)


def test_stochastic_sampling_varies(tmp_path):
    torch.manual_seed(0)
    model = Model.load(_checkpoint(tmp_path / "m.pt", torch.zeros(4)), "striker",
                       stochastic=True, hold_frames=1)
    state = torch.randn(16)

    first = model.inference(state)
    second = model.inference(state)

    assert not torch.allclose(first, second)


def test_hold_frames_repeats_the_action(tmp_path):
    torch.manual_seed(0)
    model = Model.load(_checkpoint(tmp_path / "m.pt", torch.zeros(4)), "striker",
                       stochastic=True, hold_frames=3)
    state = torch.randn(16)

    actions = [model.inference(state) for _ in range(4)]

    assert torch.allclose(actions[0], actions[1])
    assert torch.allclose(actions[1], actions[2])
    assert not torch.allclose(actions[2], actions[3])


def test_reset_resamples(tmp_path):
    torch.manual_seed(0)
    model = Model.load(_checkpoint(tmp_path / "m.pt", torch.zeros(4)), "striker",
                       stochastic=True, hold_frames=5)
    state = torch.randn(16)

    first = model.inference(state)
    model.reset()
    second = model.inference(state)

    assert not torch.allclose(first, second)


def test_model_reference_backward_compatible():
    ref = ModelReference(**{"id": "s", "file_path": "x"})
    assert ref.epsilon == 0
    assert ref.stochastic is False
    assert ref.hold_frames == 1


def test_load_accepts_the_legacy_signature(tmp_path):
    path = _checkpoint(tmp_path / "m.pt")
    model = Model.load(path, "striker", 0.1)
    assert model.epsilon == 0.1
