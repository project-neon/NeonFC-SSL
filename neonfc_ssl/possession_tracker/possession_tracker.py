import logging

from neonfc_ssl.algorithms.fsm import State


class TeamPossession(State):
    def __init__(self, color):
        super().__init__()
        self.color = color


class BoolPossessionTracker:
    def __init__(self, match, state_controller):
        self.states = {'yellow': TeamPossession('yellow'), 'blue': TeamPossession('blue')}
        self.match = match
        self.state_controller = state_controller

        self.possession_changing_events = [
            'PrepareKickOff',
            'BallPlacement',
            'PreparePenalty',
            'KickOff',
            'FreeKick',
            'Penalty'
        ]

        console_handler = logging.StreamHandler()
        log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
        self.logger = logging.Logger("StateController")
        console_handler.setFormatter(log_formatter)
        self.logger.addHandler(console_handler)

        def update_on_state(color):
            def wrapped(state, **kwargs):
                if state.current_state in self.possession_changing_events:
                    return state.current_state.color == color
                return False

            return wrapped

        def natural_change_opposites(match, **kwargs):
            dist_to_ball = lambda r: ((r.x - match.ball.x) ** 2 + (r.y - match.ball.y) ** 2) ** .5

            op_closest = dist_to_ball(min(match.opposites, key=dist_to_ball))
            my_closest = dist_to_ball(min(match.robots, key=dist_to_ball))

            if op_closest < 0.13 and op_closest < my_closest:
                return True
            return False

        def natural_change_my(match, **kwargs):
            dist_to_ball = lambda r: ((r.x - match.ball.x) ** 2 + (r.y - match.ball.y) ** 2) ** .5

            op_closest = dist_to_ball(min(match.opposites, key=dist_to_ball))
            my_closest = dist_to_ball(min(match.robots, key=dist_to_ball))

            if my_closest < 0.13 and my_closest < op_closest:
                return True
            return False

        self.states['yellow'].add_transition(self.states['blue'], update_on_state('blue'))
        self.states['blue'].add_transition(self.states['yellow'], update_on_state('yellow'))

        self.states[self.match.team_color].add_transition(self.states[self.match.opponent_color],
                                                          natural_change_opposites)
        self.states[self.match.opponent_color].add_transition(self.states[self.match.team_color], natural_change_my)

        self.possession = self.states['blue']

        self.logger.info(f"{self.get_possession()} team ball possession")

    def update(self):
        new = self.possession.update(match=self.match, state=self.state_controller)
        if self.possession != new:
            self.possession = new
            self.logger.info(f"{self.get_possession()} team has ball possession")

    def get_possession(self):
        return self.possession.color
