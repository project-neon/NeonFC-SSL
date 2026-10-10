import torch
import torch.nn as nn
from random import random
from typing import Optional


class Model(nn.Module):
    def __init__(
        self,
        layer_sizes: list[int],
        model_id: str,
        epsilon: float = 0.0,
        stochastic: bool = False,
        hold_frames: int = 1,
    ) -> None:
        super().__init__()
        assert len(layer_sizes) >= 2, "Need at least an input and output layer."

        self.id: str = model_id
        self.epsilon: float = epsilon
        # Sample from the policy's own training distribution rather than
        # always acting on the mean.
        self.stochastic: bool = stochastic
        # A fresh target every frame (~60 Hz) just averages out in the
        # P-controller, so hold each sampled action for a few frames.
        self.hold_frames: int = hold_frames

        # Written by the trainer when it exports a stochastic policy;
        # absent from older checkpoints, which play deterministically.
        self.log_std: Optional[torch.Tensor] = None

        self._held: Optional[torch.Tensor] = None
        self._hold_left: int = 0

        layers = []
        for i, (in_size, out_size) in enumerate(zip(layer_sizes[:-1], layer_sizes[1:])):
            layers.append(nn.Linear(in_size, out_size))
            is_last_layer = i == len(layer_sizes) - 2
            if not is_last_layer:
                layers.append(nn.ReLU())

        self.network = nn.Sequential(*layers)

    def inference(self, state: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            if self._held is not None and self._hold_left > 0:
                self._hold_left -= 1
                return self._held

            mean = self.network(state.float())

            if self.stochastic and self.log_std is not None:
                std = self.log_std.clamp(-20, 2).exp()
                action = torch.tanh(mean + std * torch.randn_like(mean))
            else:
                action = torch.tanh(mean)

            # Uniform override, applied after sampling.
            if self.epsilon > 0 and random() < self.epsilon:
                action = torch.empty_like(action).uniform_(-1, 1)

            self._held = action
            self._hold_left = max(0, int(self.hold_frames) - 1)
            return action

    def reset(self):
        """Drops any held action -- call at the start of an episode."""
        self._held = None
        self._hold_left = 0

    def update(self, path: str) -> None:
        checkpoint = torch.load(path, weights_only=True)
        self.load_state_dict(checkpoint["state_dict"])
        if "log_std" in checkpoint:
            self.log_std = checkpoint["log_std"]

    @classmethod
    def load(
        cls,
        path: str,
        model_id: str | None = None,
        epsilon: float = 0,
        stochastic: bool = False,
        hold_frames: int = 1,
    ) -> "Model":
        checkpoint = torch.load(path, weights_only=True)
        model = cls(
            checkpoint["layer_sizes"],
            model_id=model_id,
            epsilon=epsilon,
            stochastic=stochastic,
            hold_frames=hold_frames,
        )
        model.load_state_dict(checkpoint["state_dict"])
        if "log_std" in checkpoint:
            model.log_std = checkpoint["log_std"]
        return model
