import logging
from abc import ABC, abstractmethod
from concurrent import futures
from neonfc_ssl.strategies import Still
from neonfc_ssl.match.ssl_match import SSLMatch
from neonfc_ssl.entities import RobotCommand
from neonfc_ssl.core import Layer


class BaseCoach(Layer, ABC):
    def __init__(self, config, log_q, event_pipe):
        super().__init__("DecisionLayer", config, log_q, event_pipe)
        self.events = {}
        self.strategies = []

    def _start(self):
        self.log(logging.INFO, "Starting coach module starting ...")

        self.strategies = [Still() for _ in self.strategies]

        self._start_coach()

        self.log(logging.INFO, "Coach module started!")

    def _start_coach(self):
        pass

    @abstractmethod
    def decide(self):
        """This function takes the info about the game and decides which strategy each robot will use"""
        raise NotImplementedError("Coach needs decide implementation!")

    def _check_halt(self):
        if self._match.game_state == "Halt":
            return True
        return False

    def update(self):
        # if self._check_halt():
        #     self.commands['robots'] = [RobotCommand(robot_id=r.robot_id) for r in self._match.robots]
        #     self.new_data = True
        #     return

        self._active_robots = [robot for robot in self._robots if not robot.missing]
        self._n_active_robots = len(self._active_robots)

        self.decide()

        self.commands = []
        '''
        https://docs.python.org/3/library/concurrent.futures.html
        '''

        with futures.ThreadPoolExecutor(max_workers=self._n_active_robots) as executor:
            commands_futures = [
                executor.submit(robot.decide) for robot in self._active_robots
            ]

        for future in futures.as_completed(commands_futures):
            self.commands.append(future.result())

        self.new_data = True

    @property
    def has_possession(self):
        return self._match.possession.get_possession() == self._match.team_color
