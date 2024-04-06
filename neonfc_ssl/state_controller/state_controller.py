from neonfc_ssl.algorithms.fsm import State
from neonfc_ssl.commons.math import distance_between_points
from time import time
import logging


class GameState(State):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.start_time = None
        self.ball_initial_position = None

    def start(self, match):
        self.start_time = time()
        self.ball_initial_position = (match.ball.x, match.ball.y)


class StateController:
    def __init__(self, ref, match):
        self.ref = ref
        self.match = match
        self.current_state: GameState = None

        console_handler = logging.StreamHandler()
        log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
        self.logger = logging.Logger("StateController")
        console_handler.setFormatter(log_formatter)
        self.logger.addHandler(console_handler)

    def start(self):
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
            def trig(origin, ref, match):
                return ref._referee_message.get('command').startswith(msg)
            return trig

        def after_secs(delay):
            def trig(origin, ref, match):
                return time() - origin.start_time >= delay
            return trig

        after_10 = after_secs(10)

        def ball_moved(origin, ref, match):
            return distance_between_points(match.ball, origin.ball_initial_position) <= 0.05

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
        self.current_state.start(self.match)

    def update(self):
        next_state = self.current_state.update(self.current_state, self.ref, self.match)
        if next_state != self.current_state:
            self.logger.info(f"Changing state {self.current_state.name} -> {next_state.name}")
            self.current_state = next_state
            self.current_state.start(self.match)
