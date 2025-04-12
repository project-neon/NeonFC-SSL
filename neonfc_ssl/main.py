import json
from pip._vendor import tomli
import logging.config
import time
from multiprocessing import Pipe, Queue
from neonfc_ssl.input_layer import InputLayer
from neonfc_ssl.tracking_layer import Tracking
from neonfc_ssl.decision_layer import Decision
from neonfc_ssl.control_layer import Control
from neonfc_ssl.output_layer import OutputLayer
from neonfc_ssl.core import DebugLayer

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.core import Layer


def get_config(config_file=None):
    if config_file:
        config = json.loads(open(config_file, 'r').read())
    else:
        config = json.loads(open('config.json', 'r').read())

    return config


class Game:
    def __init__(self) -> None:
        # Load Config
        with open("config.toml", "rb") as f:
            self.config = tomli.load(f)
        # self.config = get_config()

        self.layers: list[Layer] = []
        self.layers_event: dict[str, Pipe] = {}
        self.layers_log_q = Queue()

        # Config Logger
        # self.setup_logger()

        self.logger = logging.getLogger("game")

        self.new_layer(InputLayer)
        self.new_layer(Tracking)
        self.new_layer(Decision)
        self.new_layer(Control)
        self.new_layer(OutputLayer)

    def start(self):
        self.logger.info("Starting game")

        for prev_layer, layer in zip(self.layers[:-1], self.layers[1:]):
            layer.bind_input_pipe(prev_layer.output_pipe)

        print(self.layers)

        for layer in self.layers:
            layer.start()

        self.read_log_queue()

    def read_log_queue(self):
        while True:
            log = self.layers_log_q.get()
            self.logger.log(log[1], f"{log[0]}: {log[1]}")

    def setup_logger(self):
        if (t1 := self.config['match'].get('team_1', None)) is not None and \
           (t2 := self.config['match'].get('team_2', None)) is not None and \
           (event := self.config['match'].get('event', None)) is not None:

            self.match_name = f"{t1}x{t2}@{event}"

        self.config['logger']['handlers']['main_log']['filename'] = f"logs/{self.match_name}.log.jsonl"
        self.config['logger']['handlers']['game_log']['filename'] = f"logs/{self.match_name}.gamelog.jsonl"
        logging.config.dictConfig(self.config['logger'])

    def new_layer(self, layer: type['Layer']):
        pipe_in, pipe_out = Pipe(duplex=False)
        print(self.config)
        layer_obj = layer(self.config[layer.__name__], self.layers_log_q, pipe_out)
        self.layers.append(layer_obj)
        self.layers_event[layer_obj.name] = pipe_in


def main():
    game = Game()
    game.start()


if __name__ == "__main__":
    main()
