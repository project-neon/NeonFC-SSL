import torch
import torch.nn as nn
from random import random


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

        layers = []
        for i, (in_size, out_size) in enumerate(zip(layer_sizes[:-1], layer_sizes[1:])):
            layers.append(nn.Linear(in_size, out_size))
            is_last_layer = i == len(layer_sizes) - 2
            if not is_last_layer:
                layers.append(nn.ReLU())

        self.network = nn.Sequential(*layers)

    def inference(self, state: torch.Tensor, explore: bool = True) -> torch.Tensor:
        with torch.no_grad():
            mean = self.network(state.float())

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
