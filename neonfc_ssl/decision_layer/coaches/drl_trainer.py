from .base_coach import Coach
from ..drl import ModelReference, Model, PreProcess, TCPSender, DRLStrategy, commons
from neonfc_ssl.core.event import event_callback, EventType, Event
import multiprocessing
import os
import time

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch

MODEL_INDEX = "models"
PERSISTENCE_KEY = "persistence_transformation"
OUTPUT_KEY = "output_transformation"
SENDER_CONFIG_INDEX = "sender"
MODEL_WAIT_TIMEOUT_KEY = "model_wait_timeout"
MODEL_WAIT_POLL = 0.5
MODEL_WAIT_LOG_EVERY = 10.0


class DRLCoach(Coach):

    def __init__(self, decision):
        self.__models: dict[str, Model] = {}
        self.__preprocess: PreProcess = None
        self.__last_persistence_state = None
        self.__tcp: TCPSender = None

        super().__init__(decision)

    def _start(self):
        self.__preprocess = PreProcess(
            config=self.decision.config,
            persistence_transformation=self.decision.config.get(PERSISTENCE_KEY),
            output_transformation=self.decision.config.get(OUTPUT_KEY),
        )

        self.strats = dict()

        if config := self.decision.config.get(SENDER_CONFIG_INDEX):
            self.__tcp = TCPSender.from_config(config)
            self.__tcp.start()

        timeout = self.decision.config.get(MODEL_WAIT_TIMEOUT_KEY, 0)

        for model_cfg in self.decision.config[MODEL_INDEX]:
            model_reference = ModelReference(**model_cfg)
            self.__wait_for_model_file(model_reference.file_path, timeout)
            self.__create_model(model_reference)
            self.__preprocess.bind_model(model_reference.id, model_reference.transformation)
            self.strats[model_reference.robot_id] = DRLStrategy()

    def __wait_for_model_file(self, path: str, timeout: float) -> None:
        """Blocks until the trainer has written `path`.

        On a fresh checkout the policies don't exist yet, and loading
        eagerly would kill the Decision layer while the main process keeps
        running. `model_wait_timeout` (seconds) bounds the wait; 0 means
        "don't wait", which is the old behaviour.
        """
        if os.path.exists(path):
            return

        waited = 0.0
        logged = 0.0
        while waited < timeout:
            time.sleep(MODEL_WAIT_POLL)
            waited += MODEL_WAIT_POLL
            if os.path.exists(path):
                return
            if waited - logged >= MODEL_WAIT_LOG_EVERY:
                logged = waited
                self.__logger.info("Waiting for model file (%.0fs so far): %s", waited, path)

        if not os.path.exists(path):
            raise FileNotFoundError(f"model file not found after {timeout}s: {path}")

    def _stop(self):
        if self.__tcp:
            self.__tcp.stop()

    def decide(self):
        processed_data = self.__preprocess.process(self.data)
        actions = self.__run_models(processed_data)

        self.__propagate(actions, self.__preprocess.get_persistence_outputs(processed_data))

        decision_data = self.__preprocess.apply_output_transformation(actions, self.data)

        for robot_id, strat in self.strats.items():
            strat.inject_decision(decision_data[robot_id])
            self.decision.set_strategy(self.data.robots[robot_id], strat)

    def __create_model(self, model_reference: ModelReference) -> Model:
        model = Model.load(model_reference.file_path, model_reference.id, model_reference.epsilon)
        self.__models[model_reference.id] = model
        return model

    def __run_models(self, processed_data: dict[str, 'torch.Tensor']) -> dict[str, 'torch.Tensor']:
        return {
            model_id: model.inference(processed_data[model_id])
            for model_id, model in self.__models.items()
            if model_id in processed_data
        }

    def __propagate(self, actions, data):
        current_persistence = data

        payload = {
            "next_state": (
                current_persistence.tolist() if current_persistence is not None else None
            ),
            "cur_state": self.__last_persistence_state,
            "actions": {k: v.tolist() for k, v in actions.items()},
        }

        self.__last_persistence_state = (
            current_persistence.tolist() if current_persistence is not None else None
        )

        self.__tcp.send(payload)

    @event_callback(EventType.MODEL_UPDATE)
    def model_update(self, event: Event):
        for model_cfg in event.event_data[MODEL_INDEX]:
            model_reference = ModelReference(**model_cfg)
            if model := self.__models.get(model_reference.id):
                model.update(model_reference.file_path)

    @event_callback(EventType.EPSILON_GREEDY)
    def epsilon_greedy(self, event: Event):
        for model_cfg in event.event_data[MODEL_INDEX]:
            model_reference = ModelReference(**model_cfg)
            if model := self.__models.get(model_reference.id):
                model.epsilon = model_reference.epsilon
