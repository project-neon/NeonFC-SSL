import math
import torch
import torch.nn as nn
from random import random

# Per-feature normalization. Matches the state layout produced by
# input_transformation: N robots x (x, y, theta, vx, vy, vtheta), then
# ball x (x, y, vx, vy). Field half-dimensions match DistanceToBall's
# convention. V_MAX/VTHETA_MAX are placeholders -- confirm against the
# sim's actual speed limits before trusting these.
X_MAX, Y_MAX = 9.0, 6.0
V_MAX = 4.0
VTHETA_MAX = 10.0


class Model(nn.Module):
    def __init__(self, layer_sizes: list[int], model_id: str, epsilon: float,
                 log_std: torch.Tensor | None = None) -> None:
        super().__init__()
        assert len(layer_sizes) >= 2, "Need at least an input and output layer."

        self.id: str = model_id
        self.epsilon: float = epsilon
        # Falls back to zeros (std=1) if an older checkpoint has no
        # log_std yet, so this stays backward compatible.
        self.log_std: torch.Tensor = (
            log_std if log_std is not None else torch.zeros(layer_sizes[-1])
        )
        # Registered as a buffer so .to(device) moves it along with the
        # network's own parameters.
        self.register_buffer("state_scale", self._default_state_scale(layer_sizes[0]))

        layers = []
        for i, (in_size, out_size) in enumerate(zip(layer_sizes[:-1], layer_sizes[1:])):
            layers.append(nn.Linear(in_size, out_size))
            is_last_layer = i == len(layer_sizes) - 2
            if not is_last_layer:
                layers.append(nn.ReLU())

        self.network = nn.Sequential(*layers)

    @staticmethod
    def _default_state_scale(state_dim: int) -> torch.Tensor:
        """Builds the per-feature scale vector from the known state
        layout: N robots x (x, y, theta, vx, vy, vtheta), then ball x
        (x, y, vx, vy)."""
        per_robot = torch.tensor([X_MAX, Y_MAX, math.pi, V_MAX, V_MAX, VTHETA_MAX])
        ball = torch.tensor([X_MAX, Y_MAX, V_MAX, V_MAX])
        n_robots = (state_dim - ball.numel()) // per_robot.numel()
        scale = torch.cat([per_robot] * n_robots + [ball])
        assert scale.numel() == state_dim, (
            f"state_dim {state_dim} doesn't match the expected robot/ball "
            f"layout ({n_robots} robots -> {scale.numel()} features)"
        )
        return scale

    def _normalize(self, state: torch.Tensor) -> torch.Tensor:
        return state.float() / self.state_scale

    def inference(self, state: torch.Tensor, explore: bool = True) -> torch.Tensor:
        with torch.no_grad():
            mean = self.network(self._normalize(state))

            if explore:
                std = self.log_std.exp().to(mean.device)
                action = torch.tanh(torch.distributions.Normal(mean, std).sample())
            else:
                action = torch.tanh(mean)

            if self.epsilon > 0 and random() < self.epsilon:
                action = torch.empty_like(action).uniform_(-1, 1)

            return action

    def update(self, path: str) -> None:
        checkpoint = torch.load(path, weights_only=True)
        self.load_state_dict(checkpoint["state_dict"])
        if "log_std" in checkpoint:
            self.log_std = checkpoint["log_std"]

    @classmethod
    def load(cls, path: str, model_id: str | None = None, epsilon: float = 0) -> "Model":
        checkpoint = torch.load(path, weights_only=True)
        model = cls(
            checkpoint["layer_sizes"],
            model_id=model_id,
            epsilon=epsilon,
            log_std=checkpoint.get("log_std"),
        )
        model.load_state_dict(checkpoint["state_dict"])
        return model
