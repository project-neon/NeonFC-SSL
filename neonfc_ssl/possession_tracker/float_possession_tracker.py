import logging
from collections import deque
import numpy as np


class FloatPossessionTracker:
    def __init__(self, match, state_controller):
        self.poss = 0
        self.last_poss = deque([], maxlen=10)
        self.match = match
        self.state_controller = state_controller
        self.current_closest = None

        self.in_ball_contact = False
        self.contact_start_position = np.array([0, 0])

        self.logger = logging.getLogger("match")

        self.logger.info(f"{self.get_possession()} team ball possession")

    def update(self):
        time_to_ball = lambda r: r.time_to_ball(self.match.ball) if r is not None else float('inf')
        sq_dist_to_ball = lambda r: np.sum(np.square(np.array(r)-self.match.ball))

        op_closest = min(self.match.active_opposites, key=time_to_ball, default=None)
        my_closest = min(self.match.active_robots, key=time_to_ball, default=None)

        op_time = time_to_ball(op_closest)
        my_time = time_to_ball(my_closest)

        current_balance = op_time - my_time
        self.current_closest = my_closest
        self.last_poss.append(current_balance)
        self.poss = sum(self.last_poss)/len(self.last_poss)

        if not self.in_ball_contact and sq_dist_to_ball(my_closest) <= 0.0144: # (robot_radius + 0.03m)^2
            self.in_ball_contact = True
            self.contact_start_position = np.array(my_closest)

        if self.in_ball_contact and not sq_dist_to_ball(my_closest) <= 0.0196: # (robot_radius + 0.05m)^2
            self.in_ball_contact = False

    def get_possession(self):
        return self.match.team_color if self.poss > 0 else self.match.opponent_color
