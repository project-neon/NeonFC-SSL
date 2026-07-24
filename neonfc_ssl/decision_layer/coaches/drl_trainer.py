from .base_coach import Coach
from ..drl import ModelReference, Model, PreProcess, TCPSender, DRLStrategy, commons
from neonfc_ssl.core.event import event_callback, EventType, Event
import multiprocessing

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch

MODEL_INDEX = "models"
PERSISTENCE_KEY = "persistence_transformation"
OUTPUT_KEY = "output_transformation"
SENDER_CONFIG_INDEX = "sender"


class DRLCoach(Coach):

    def __init__(self, decision):
        self.__models: dict[str, Model] = {}
        self.__preprocess: PreProcess = None
        self.__last_persistence_state = None
        self.__tcp: TCPSender = None

        super().__init__(decision)

    def _start(self):
        self.__preprocess = PreProcess(
            persistence_transformation=self.decision.config.get(PERSISTENCE_KEY),
            output_transformation=self.decision.config.get(OUTPUT_KEY),
        )

        self.strats = {
            commons.GOALKEEPER_ID: DRLStrategy(),
            commons.STRIKER_ID: DRLStrategy(),
        }

        if config := self.decision.config.get(SENDER_CONFIG_INDEX):
            self.__tcp = TCPSender.from_config(config)
            self.__tcp.start()

        for model_cfg in self.decision.config[MODEL_INDEX]:
            model_reference = ModelReference(**model_cfg)
            self.__create_model(model_reference)
            self.__preprocess.bind_model(model_reference.id, model_reference.transformation)

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
        model = Model.load(model_reference.file_path, model_reference.id)
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
