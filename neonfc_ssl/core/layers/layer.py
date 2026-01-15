from typing import TYPE_CHECKING, Any
from multiprocessing import Process, Pipe, Queue
from multiprocessing.connection import Connection
from abc import ABC, abstractmethod
from time import time
import logging

from neonfc_ssl.core.logger import LayerHandler
from neonfc_ssl.core.event import EventHandler


LAYER_START_ERROR_LOG = "Exception during layer {} start"
BEGIN_START_LOG = "Starting layer {}"
END_START_LOG = "Layer {} started"
LAYER_IDLE_LIMIT_LOG = "Layer {} idle time limit exceeded, forcing start on old data {}"
LAYER_STEP_TIME_LIMIT_LOG = "Layer {} under-performing, {} Hz"


class Layer(Process):
    IDLE_LIMIT = 1 / 60  # s (60 Hz)

    def __init__(self, name: str, config: dict, log_q: Queue):
        super().__init__(daemon=True)
        self.name = name
        self.config = config

        # process communication variables
        self.logger = self.__setup_logger(
            log_q
        )  # send logs to the main process and eventually to the interface
        self.__events_q = Queue()  # receive events from the main process possibly originating from the interface
        self.__input: Connection = None  # last layer pipe tail in the pipeline
        self.__output_tail, self.__output_head = Pipe(
            duplex=False
        )  # output pipe in the pipeline (to the next layer)
        self.__event_handler = EventHandler()
        self.__event_handler.register_from_instance(self)

        # layer state variables
        self.__running = False
        self.__started = True
        self.__new_data = False
        self.__current_process_start = time()
        self.__last_finished_process = time()

        self._previous_layer = ""

        self.__last_data = None

    @property
    def subscriptions(self):
        return self.__event_handler.subscriptions()

    @property
    def events_q(self):
        return self.__events_q

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

    def run(self):
        self.logger.info(BEGIN_START_LOG.format(self.name))
        try:
            self._start()
        except Exception as e:
            self.logger.error(LAYER_START_ERROR_LOG.format(self.__class__.__name__))
            raise e
        self.__started = True
        self.logger.info(END_START_LOG.format(self.name))
        while True:
            self.__process_events()

            self.__fetch_new_data()

            if self.__new_data:
                self.__do_execution()

            elif (dt := time() - self.__last_finished_process) >= self.IDLE_LIMIT and self.__last_data is not None:
                self.logger.info(LAYER_IDLE_LIMIT_LOG.format(self.__class__.__name__, 1/dt))
                self.__do_execution()

    def __process_events(self):
        while not self.__events_q.empty():
            event = self.__events_q.get(timeout=0.01)
            self.__event_handler(event)

    def __do_execution(self):
        self.__running = True
        step_execution_begin_time = time()
        self.__send(self._step(self.__last_data))
        step_execution_end_time = time()
        self.__new_data = False
        if (dt := step_execution_end_time - step_execution_begin_time) >= 1/self.IDLE_LIMIT:
            self.logger.warning(LAYER_STEP_TIME_LIMIT_LOG.format(self.__class__.__name__, 1/dt))
        self.__last_finished_process = step_execution_end_time

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
