from typing import TYPE_CHECKING, Any
import time
from neonfc_ssl.core import Layer
from neonfc_ssl.vision.gr_sim_vision import GrSimVision
from neonfc_ssl.vision.auto_ref_vision import AutoRefVision
from neonfc_ssl.referee.ssl_game_controller import SSLGameControllerReferee
from neonfc_ssl.input_l.input_data import InputData


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