import json
import os
from pip._vendor import tomli
import logging.config
import time
import socket
import sys
import argparse
from threading import Thread
from multiprocessing import Pipe, Queue
from neonfc_ssl.input_layer import InputLayer
from neonfc_ssl.tracking_layer import Tracking
from neonfc_ssl.decision_layer import Decision
from neonfc_ssl.control_layer import Control
from neonfc_ssl.output_layer import OutputLayer
from neonfc_ssl.core import DebugLayer, event
from neonfc_ssl.core.logger import setup_logging

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from neonfc_ssl.core import Layer
    from multiprocessing.connection import Connection


class Game:
    def __init__(self, args) -> None:
        # Load Config
        with args.profile as f:
            self.config = tomli.load(f)

        if args.color:
            self.config["Tracking"]["Color"] = args.color
        if args.side:
            self.config["InputLayer"]["side"] = args.side

        self.layers: list[Layer] = []
        self.layers_event: dict[str, 'Connection'] = {}
        self.layers_log_q = Queue()

        # Config Logger
        setup_logging(self.config['Game'])

        self.logger = logging.getLogger("game")

        self.event_engine = event.EventEngine()
        self.event_engine.create_socket(self.config['Game']["host"], self.config['Game']["input_port"])

        self.new_layer(InputLayer)
        self.new_layer(Tracking)
        self.new_layer(Decision)
        self.new_layer(Control)
        self.new_layer(OutputLayer)

        self.output_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.__intervals = {}

    def send_udp(self, msg):
        self.output_socket.sendto(msg, (self.config['Game']['host'], self.config['Game']['output_port']))

    def send_architecture(self):
        msg = {'type': 'architecture', 'data': {'layers': [layer.name for layer in self.layers]}}
        self.send_udp(json.dumps(msg))

    def start(self):
        self.logger.info("Starting game")

        for prev_layer, layer in zip(self.layers[:-1], self.layers[1:]):
            layer.bind_input_pipe(prev_layer.output_pipe)

        for layer in self.layers:
            layer.start()

        self.read_log_queue()

    def read_log_queue(self):
        while True:
            record = self.layers_log_q.get()
            self.logger.handle(record)
            # self.logger.log(log["type"], f"{log['source']}: {log}")

    def new_layer(self, layer: type['Layer']):
        layer_obj = layer(self.config[layer.__name__], self.layers_log_q)
        self.layers.append(layer_obj)

        for event_type in layer_obj.subscriptions:
            self.event_engine.subscribe(event_type, layer_obj.events_q)


def main(args=None):
    if not args:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--profile",
        help="the config file",
        default="config.toml",
        type=argparse.FileType(mode="rb"),
    )
    parser.add_argument(
        "-c", "--color",
        help="the team color (will overwrite the config file)",
        default=None,
        choices=["yellow", "blue"]
    )
    parser.add_argument(
        "-s", "--side",
        help="the team goalkeeper side (will overwrite the config file)",
        default=None,
        choices=["left", "right"]
    )
    w = os.get_terminal_size().columns
    print("=" * w)
    print(r"""⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀                             
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣄⡀⠀⠀                             
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣦⠀⠀⠀⠀⠀⠀⠀⣾⠋⠙⣷⠀⠀                             
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣦⣀⢀⣿⣿⣇⣀⣀⣀⠀⠀⢸⡟⠀⢰⣿⣦⠀                             
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣼⡇⠀⠈⠻⠋⠀                             
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⠀⠀⠀                              
⠀⠰⣤⣀⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⣿⣿⠟⢿⣿⣿⠋⠁⣾⣿⣿⣷⡄⠀                              
⠀⠀⠘⣿⣿⣶⣴⣿⣿⣿⣿⣿⣿⣿⡏⢹⡟⠀⣿⣿⣿⣄⠀⠈⣡⣿⠟⠀_                  _____ ____  
⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣀⠘⢷⣄⠉⠻⣿⣿⣿⣿⡿⠃⠀|⠀|⠀___⠀⠀___⠀⠀_⠀__⠀|⠀⠀___/⠀___| 
⠀⠀⠚⢻⣿⣿⠿⠛⠻⢿⣿⣿⣿⣿⣿⣷⣴⣿⣿⣦⣿⣿⣿⠏⠀⠀\|⠀|/⠀_⠀\/⠀_⠀\|⠀'_⠀\|⠀|_⠀|⠀|     
⠀⠀⣠⠿⠋⠁⠀⠀⠀⠀⠈⠙⣻⣿⣿⣿⣿⣿⡿⣿⣿⡟⠁|⠀|\⠀⠀|⠀⠀__/⠀(_)⠀|⠀|⠀|⠀|⠀⠀_||⠀|___  
⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠘⣻⣿⣿⣿⣿⠿⢿⣷⣄⡉⠀⠀|_|⠀\_|\___|\___/|_|⠀|_|_|⠀⠀⠀\____| 
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⣿⡟⠁⠀⠀⠈⠙⠻⠿⣶⣶⣶⣶⠀⠀                               
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀                              
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀""")
    print("=" * w)
    args = parser.parse_args(args)

    game = Game(args)
    game.start()


if __name__ == "__main__":
    main()
