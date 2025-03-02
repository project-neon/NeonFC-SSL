import json
import atexit
import logging.config
import time
from comm.serial_comm import SerialComm
from comm.grsim_comm import GrComm
from control import Control

from multiprocessing import Pipe, Queue
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.core import Layer

from neonfc_ssl.input_layer import InputLayer
from neonfc_ssl.match import SSLMatch
from neonfc_ssl.decision_layer import Decision
from neonfc_ssl.core import DebugLayer



def get_config(config_file=None):
    if config_file:
        config = json.loads(open(config_file, 'r').read())
    else:
        config = json.loads(open('config.json', 'r').read())

    return config


class Game:
    def __init__(self) -> None:
        # Load Config
        self.config = get_config()
        self.match_name = "Test"
        self.t1 = self.config['match'].get('team_1', None)
        self.t2 = self.config['match'].get('team_2', None)
        self.event = self.config['match'].get('event', None)

        self.match_name = f"{self.t1}x{self.t2}@{self.event}" if self.t1 and self.t2 and self.event else "test"

        self.layers: list[Layer] = []
        self.layers_event: dict[str, Pipe] = {}
        self.layers_log_q = Queue()

        # Config Logger
        self.setup_logger()

        self.logger = logging.getLogger("game")

        # Input Layer
        # self.ssl_vison = GrSimVision(self.config)
        # self.auto_ref = AutoRefVision(self.config)
        # self.referee = SSLGameControllerReferee()

        # self.vision = self.auto_ref
        # self.geometry = self.ssl_vison

        # Tracking Layer
        # self.match = SSLMatch(self)

        # Decision Layer
        # self.coach = COACHES["SimpleCoach"](self)

        # Control Layer
        self.control = Control(self)

        # Output Layer
        self.comm = SerialComm(self)

        # Register exit handler
        atexit.register(self.stop_threads)

        self.new_layer(InputLayer)
        self.new_layer(SSLMatch)
        self.new_layer(Decision)
        self.new_layer(DebugLayer)
        # self.new_layer(SSLMatch)

    def start(self):
        self.logger.info("Starting game")
        # info = {"t1": self.t1, "t2": self.t2, "event": self.event, "vision": type(self.vision).__name__}
        # self.logger.game("game meta", extra={"type": 'ssl'})
        # self.logger.game("game begin", extra=info)
        # info["coach"] = "TestCoach"
        # self.logger.decision("game begin", extra=info)

        for prev_layer, layer in zip(self.layers[:-1], self.layers[1:]):
            layer.bind_input_pipe(prev_layer.output_pipe)

        print(self.layers)

        for layer in self.layers:
            layer.start()

        self.read_log_queue()

    def read_log_queue(self):
        while True:
            log = self.layers_log_q.get()
            print(log)

    def setup_logger(self):
        if (t1 := self.config['match'].get('team_1', None)) is not None and \
           (t2 := self.config['match'].get('team_2', None)) is not None and \
           (event := self.config['match'].get('event', None)) is not None:

            self.match_name = f"{t1}x{t2}@{event}"

        self.config['logger']['handlers']['main_log']['filename'] = f"logs/{self.match_name}.log.jsonl"
        self.config['logger']['handlers']['game_log']['filename'] = f"logs/{self.match_name}.gamelog.jsonl"
        logging.config.dictConfig(self.config['logger'])

    def stop_threads(self):
        return
        self.ssl_vison.stop()
        self.auto_ref.stop()
        self.referee.stop()

    def new_layer(self, layer: type['Layer']):
        pipe_in, pipe_out = Pipe(duplex=False)
        layer_obj = layer(self.config, self.layers_log_q, pipe_out)
        self.layers.append(layer_obj)
        self.layers_event[layer_obj.name] = pipe_in

    def update(self):
        while True:
            try:
                if self.vision.new_data and self.geometry.any_geometry:
                    t = [time.time()]
                    self.match.update()
                    t.append(time.time())
                    self.coach.update()
                    t.append(time.time())
                    self.control.update()
                    t.append(time.time())
                    if self.referee.is_halted():
                        self.comm.freeze()
                    else:
                        self.comm.update()
                    # self.comm.update()
                    t.append(time.time())
                    if self.config['match'].get('time_logging', False):
                        self.logger.info(f"total:  {1/(t[4]-t[0]):.2f} Hz")
                        self.logger.info(f"match:  {1/(t[1]-t[0]):.2f} Hz")
                        self.logger.info(f"coach:  {1/(t[2]-t[1]):.2f} Hz")
                        self.logger.info(f"control:  {1/(t[3]-t[2]):.2f} Hz")
                        self.logger.info(f"comm:  {1/(t[4]-t[3]):.2f} Hz")

            except KeyboardInterrupt:
                break


if __name__ == "__main__":
    game = Game()
    game.start()
