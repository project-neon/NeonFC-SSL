from neonfc_ssl.algorithms.fsm import State
from neonfc_ssl.commons.math import distance_between_points
from time import time
from dataclasses import dataclass
import logging
from typing import Optional


class GameState(State):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.start_time = None
        self.ball_initial_position = None
        self.color = None
        self.position = None
        self.last_state: Optional[LastStateInfo] = None

    def start(self, match, color, position, last_state):
        self.start_time = time()
        self.ball_initial_position = (match.ball.x, match.ball.y)
        self.color = color
        self.position = position
        self.last_state = last_state


@dataclass
class LastStateInfo:
    first_touch: bool
    first_touch_id: int


class StateController:
    def __init__(self, match):
        self._match = match
        self.current_state = None

        console_handler = logging.StreamHandler()
        log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
        self.logger = logging.Logger("StateController")
        console_handler.setFormatter(log_formatter)
        self.logger.addHandler(console_handler)

        self.last_state: Optional[LastStateInfo] = None

        # Following appendix B found in: https://robocup-ssl.github.io/ssl-rules/sslrules.pdf
        self.states = {
            'Halt': GameState('Halt'),
            'TimeOut': GameState('TimeOut'),
            'Stop': GameState('Stop'),
            'PrepareKickOff': GameState('PrepareKickOff'),
            'BallPlacement': GameState('BallPlacement'),
            'PreparePenalty': GameState('PreparePenalty'),
            'KickOff': GameState('KickOff'),
            'FreeKick': GameState('FreeKick'),
            'Penalty': GameState('Penalty'),
            'Run': GameState('Run')
        }

        def on_ref_message(msg):
            def trig(cmd, **kwargs):
                return cmd.startswith(msg)
            return trig

        def after_secs(delay):
            @self.save_info(False)
            def trig(origin, **kwargs):
                return time() - origin.start_time >= delay
            return trig

        after_10 = after_secs(10)

        @self.save_info(True)
        def ball_moved(ball, **kwargs):
            return ball.get_speed() >= 0.05

        # _ -> Halt
        halt = on_ref_message('HALT')

        for name, state in self.states.items():
            if name == 'Halt':
                continue
            state.add_transition(self.states['Halt'], halt)

        # _ -> Stop
        stop = on_ref_message('STOP')

        # Halt -> Stop
        self.states['Halt'].add_transition(self.states['Stop'], stop)

        # Timeout -> Stop
        self.states['TimeOut'].add_transition(self.states['Stop'], stop)

        # BallPlacement -> Stop
        self.states['BallPlacement'].add_transition(self.states['Stop'], stop)

        # Run -> Stop
        self.states['Run'].add_transition(self.states['Stop'], stop)

        # Penalty -> Stop
        self.states['Penalty'].add_transition(self.states['Stop'], after_10)

        # Stop -> PrepareKickOff
        self.states['Stop'].add_transition(self.states['PrepareKickOff'], on_ref_message('PREPARE_KICKOFF'))

        # Stop -> BallPlacement
        self.states['Stop'].add_transition(self.states['BallPlacement'], on_ref_message('BALL_PLACEMENT'))

        # Stop -> PreparePenalty
        self.states['Stop'].add_transition(self.states['PreparePenalty'], on_ref_message('PREPARE_PENALTY'))

        # Stop -> FreeKick
        self.states['Stop'].add_transition(self.states['FreeKick'], on_ref_message('DIRECT_FREE'))

        # Stop -> TimeOut
        self.states['Stop'].add_transition(self.states['TimeOut'], on_ref_message('TIMEOUT'))

        # Stop -> Run
        self.states['Stop'].add_transition(self.states['Run'], on_ref_message('FORCE_START'))

        # PrepareKickOff -> KickOff
        self.states['PrepareKickOff'].add_transition(self.states['KickOff'], on_ref_message('NORMAL_START'))

        # BallPlacement -> FreeKick
        self.states['BallPlacement'].add_transition(self.states['FreeKick'], on_ref_message('CONTINUE'))

        # PreparePenalty -> Penalty
        self.states['PreparePenalty'].add_transition(self.states['Penalty'], on_ref_message('NORMAL_START'))

        # KickOff -> Run
        self.states['KickOff'].add_transition(self.states['Run'], ball_moved)
        self.states['KickOff'].add_transition(self.states['Run'], after_10)

        # FreeKick -> Run
        self.states['FreeKick'].add_transition(self.states['Run'], ball_moved)
        self.states['FreeKick'].add_transition(self.states['Run'], after_10)

        self.current_state = self.states['Halt']
        self.current_state.start(self._match, None, None, None)

    def save_info(self, touched):
        def wrapper(f):
            def wrapped(poss, *args, **kwargs):
                out = f(*args, **kwargs)
                if out:
                    self.last_state = LastStateInfo(touched, poss.current_closest.robot_id if touched else None)
                return out
            return wrapped
        return wrapper

    def update(self, ref):
        next_state = self.current_state.update(
            origin=self.current_state,
            cmd=ref['command'],
            ball=self._match.ball,
            poss=self._match.possession
        )

        # TODO: This lacks some way to reset the last touch info when the robot that did the initial touch can touch again

        if next_state != self.current_state:
            self.logger.info(f"Changing state {self.current_state.name} -> {next_state.name}")
            self.current_state = next_state
            self.current_state.start(self._match, ref['team'], ref['pos'], self.last_state)
            self.last_state = None

    def is_stopped(self):
        return self.current_state.name in ["Stop", "PrepareKickOff", "BallPlacement", "PreparePenalty"]

    def __eq__(self, other):
        return self.current_state.name == other

