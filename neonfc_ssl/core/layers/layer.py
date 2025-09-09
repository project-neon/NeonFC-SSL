from typing import TYPE_CHECKING, Any
from multiprocessing import Process, Pipe, Queue
from multiprocessing.connection import Connection
from abc import ABC, abstractmethod
from time import time
import logging
from neonfc_ssl.core.logger import LayerHandler


class Layer(Process):
    IDLE_LIMIT = 1/60  # s (60 Hz)

    def __init__(self, name: str, config: dict, log_q: Queue, event_pipe: Pipe):
        super().__init__(daemon=True)
        self.name = name
        self.config = config

        # process communication variables
        self.logger = self.__setup_logger(log_q)  # send logs to the main process and eventually to the interface
        self.__events_pipe = event_pipe  # receive events from the main process possibly originating from the interface
        self.__input: Connection = None  # last layer pipe tail in the pipeline
        self.__output_tail, self.__output_head = Pipe(duplex=False)  # output pipe in the pipeline (to the next layer)

        # layer state variables
        self.__running = False
        self.__started = True
        self.__new_data = False
        self.__current_process_start = time()
        self.__last_finished_process = time()

        self._previous_layer = ""

        self.__last_data = None

    def __setup_logger(self, log_q: Queue) -> logging.Logger:
        lgg = logging.getLogger(self.name)
        lgg.setLevel(logging.NOTSET)
        lgg.propagate = False  # to avoid double logging
        lgg.addHandler(LayerHandler(log_q))

        return lgg

    def bind_input_pipe(self, pipe):
        self.__input = pipe

    def __fetch_new_data(self):
        if self.__input is None:  # when the layers uses input from outside sources
            self.__new_data = True
            return

        while self.__input.poll():
            self.__new_data = True
            self.__last_data = self.__input.recv()

    def __fetch_event(self):
        pass

    def run(self):
        self.logger.info("Starting layer {}".format(self.name))
        self._start()
        self.__started = True
        self.logger.info("{} layer started.".format(self.name))
        while True:
            self.__fetch_event()

            # TODO: check if should kill
            # if ...:
            #   break

            self.__fetch_new_data()

            if self.__new_data:
                self.__running = True
                self.__send(self._step(self.__last_data))
                self.__last_finished_process = time()

            elif time() - self.__last_finished_process >= self.IDLE_LIMIT and self.__last_data is not None:
                self.__running = True
                self.logger.warning("Exceeded idle limit, forcing start on old data")
                self.__send(self._step(self.__last_data))
                self.__last_finished_process = time()

            self.__running = False

    def __send(self, data):
        if data is not None:
            self.__output_head.send(data)

    @abstractmethod
    def _step(self, data) -> Any:
        pass

    @abstractmethod
    def _start(self):
        pass

    @property
    def previous_layer(self):
        return self._previous_layer

    @property
    def output_pipe(self):
        return self.__output_tail

    def __repr__(self):
        return "<Layer {}>".format(self.name)
