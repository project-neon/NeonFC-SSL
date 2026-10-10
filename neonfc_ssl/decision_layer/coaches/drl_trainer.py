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
        self.__last_state = None
        self.__last_actions = None
        self.__tcp: TCPSender = None
        self.__logger = None

        super().__init__(decision)

    def _start(self):
        self.__logger = self.decision.logger
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

        timeout = self.decision.config.get(MODEL_WAIT_TIMEOUT_KEY, 0)

        for model_cfg in self.decision.config[MODEL_INDEX]:
            model_reference = ModelReference(**model_cfg)
            self.__wait_for_model_file(model_reference.file_path, timeout)
            self.__create_model(model_reference)
            self.__preprocess.bind_model(model_reference.id, model_reference.transformation)

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
        model = Model.load(
            model_reference.file_path,
            model_reference.id,
            model_reference.epsilon,
            model_reference.stochastic,
            model_reference.hold_frames,
        )
        self.__models[model_reference.id] = model
        return model

    def __run_models(self, processed_data: dict[str, 'torch.Tensor']) -> dict[str, 'torch.Tensor']:
        return {
            model_id: model.inference(processed_data[model_id])
            for model_id, model in self.__models.items()
            if model_id in processed_data
        }

    def __propagate(self, actions, data):
        state_list = data.tolist() if data is not None else None
        actions_list = {k: v.tolist() for k, v in actions.items()}

        if state_list is not None and state_list == self.__last_state:
            # The layer re-runs its step on stale data when no new frame
            # has arrived. Nothing moved, so emitting (s, a, s) again
            # would teach the critic that an action had no effect.
            return

        # The action that *caused* this transition is the one computed on
        # the previous tick, not this one: a_t was sampled from s_{t-1}.
        if self.__tcp is not None and self.__last_state is not None and state_list is not None:
            self.__tcp.send({
                "cur_state": self.__last_state,
                "actions": self.__last_actions,
                "next_state": state_list,
            })

        self.__last_state = state_list
        self.__last_actions = actions_list

    def reset_episode(self):
        """Called when the harness starts a new episode.

        Without this the first transition of an episode would be glued
        to the last state of the previous one.
        """
        self.__last_state = None
        self.__last_actions = None
        for model in self.__models.values():
            model.reset()

    @event_callback(EventType.MODEL_UPDATE)
    def model_update(self, event: Event):
        for model_cfg in event.event_data[MODEL_INDEX]:
            model_reference = ModelReference(**model_cfg)
            if model := self.__models.get(model_reference.id):
                model.update(model_reference.file_path)
                # Only override what the event actually carried: the
                # trainer omits these keys unless it wants them changed,
                # and the dataclass defaults would otherwise reset the
                # current settings on every weight update.
                for key in ("epsilon", "stochastic", "hold_frames"):
                    if key in model_cfg:
                        setattr(model, key, model_cfg[key])

    @event_callback(EventType.EPSILON_GREEDY)
    def epsilon_greedy(self, event: Event):
        for model_cfg in event.event_data[MODEL_INDEX]:
            model_reference = ModelReference(**model_cfg)
            if model := self.__models.get(model_reference.id):
                model.epsilon = model_reference.epsilon
