from typing import Any
import time
from dataclasses import asdict
from neonfc_ssl.core import Layer
from neonfc_ssl.core.logger import TRACKING
from .sockets.gr_sim_vision import GrSimVision
from .sockets.auto_ref_vision import AutoRefVision
from .sockets.ssl_game_controller import SSLGameControllerReferee
from .input_data import InputData


class InputLayer(Layer):
    def __init__(self, config, log_q, event_pipe):
        super().__init__("InputLayer", config, log_q, event_pipe)

        if self.config['side'] != 'left' and self.config['side'] != 'right':
            raise ValueError("side must be either 'left' or 'right'")

        self.ssl_vison = GrSimVision(self.config, self.log)
        self.auto_ref = AutoRefVision(self.config, self.log)
        self.referee = SSLGameControllerReferee(self.config, self.log)

        self.use_ref_vision = self.config["use_ref_vision"]

    def _step(self, data) -> Any:
        if self.use_ref_vision:
            while not self.auto_ref.new_data:
                time.sleep(0.01)
            vision_data = self.auto_ref.get_last_frame()

        else:
            while not self.ssl_vison.new_data:
                time.sleep(0.01)
            vision_data = self.ssl_vison.get_last_frame()

        geometry = self.ssl_vison.get_geometry()
        # self.log(GAME, {
        #     "type": "geometry",
        #     "content": asdict(geometry)
        # })
        gc = self.referee.get_data()

        return InputData(
            entities=vision_data,
            geometry=geometry,
            game_controller=gc
        )

    def _start(self):
        self.ssl_vison.start()
        self.auto_ref.start()
        self.referee.start()

        while not self.ssl_vison.any_geometry:
            time.sleep(0.1)
