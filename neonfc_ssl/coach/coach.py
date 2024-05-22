from abc import ABC, abstractmethod
from concurrent import futures
from neonfc_ssl.entities import RobotCommand


class BaseCoach(ABC):
    def __init__(self, game):
        self._game = game

        # Tracking Layer Classes
        self._match = None

        # Other Useful Parameters
        self._active_robots = None
        self._n_active_robots = None
        self._robots = None

        self.commands = None
        self.new_data = False

    def start(self):
        print("Starting coach module starting ...")

        # Last Layer Classes
        self._match = self._game.match
        self._robots = self._match.robots

        self.commands = {'team': {
            'color': self._match.team_color
        }, 'robots': []}

        print("Coach module started")

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

        self._active_robots = ...  # TODO: create active robots list
        self._active_robots = self._robots
        self._n_active_robots = len(self._active_robots)

        self.decide()

        self.commands['robots'] = []
        '''
        https://docs.python.org/3/library/concurrent.futures.html
        '''

        with futures.ThreadPoolExecutor(max_workers=self._n_active_robots) as executor:
            commands_futures = [
                executor.submit(robot.decide) for robot in self._active_robots
            ]

        for future in futures.as_completed(commands_futures):
            self.commands['robots'].append(future.result())

        self.new_data = True

    @property
    def has_possession(self):
        return self._match.possession.get_possession() == self._match.team_color
