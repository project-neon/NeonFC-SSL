import logging
from collections import deque


class FloatPossessionTracker:
    def __init__(self, match, state_controller):
        self.poss = 0
        self.last_poss = deque([], maxlen=10)
        self.match = match
        self.state_controller = state_controller
        self.current_closest = None

        console_handler = logging.StreamHandler()
        log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
        self.logger = logging.Logger("StateController")
        console_handler.setFormatter(log_formatter)
        self.logger.addHandler(console_handler)

        self.logger.info(f"{self.get_possession()} team ball possession")

    def update(self):
        dist_to_ball = lambda r: r.time_to_ball(self.match.ball)

        op_closest = min(self.match.active_opposites, key=dist_to_ball)
        my_closest = min(self.match.active_robots, key=dist_to_ball)

        op_time = dist_to_ball(op_closest)
        my_time = dist_to_ball(my_closest)

        current_balance = op_time - my_time
        self.current_closest = my_closest
        self.last_poss.append(current_balance)
        self.poss = sum(self.last_poss)/len(self.last_poss)

    def get_possession(self):
        return self.match.team_color if self.poss > 0 else self.match.opponent_color
