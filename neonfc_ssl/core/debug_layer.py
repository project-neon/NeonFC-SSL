from typing import Any
from neonfc_ssl.core import Layer


class DebugLayer(Layer):
    IDLE_LIMIT = 1/60  # s (60 Hz)

    def __init__(self, config, log_q, event_pipe):
        super().__init__("DebugLayer", config, log_q, event_pipe)
        self._previous_layer = "MatchLayer"

    def _step(self, data) -> Any:
        if data is not None:
            print(data)

    def _start(self):
        pass