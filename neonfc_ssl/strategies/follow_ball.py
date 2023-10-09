import numpy as np

def unit_vector(vector):
    """ Returns the unit vector of the vector."""
    if np.linalg.norm(vector) == 0:
        return np.array([0, 0])
    return vector / np.linalg.norm(vector)

def to_point(target, robot, decay=lambda x: 1, max_radius=1, speed=2):
    to_target = np.subtract(target, robot)

    to_taget_scalar = np.linalg.norm(to_target)

    to_target_norm = unit_vector(to_target)

    to_target_scalar_norm = max(0, min(1, to_taget_scalar/max_radius))

    force = decay(to_target_scalar_norm)

    return [
            to_target_norm[0] * force * speed,
            to_target_norm[1] * force * speed
        ]


class FollowPoint():
    def __init__(self, robot):
        self.name = 'FOLLOW-BALL'
        self.match = robot.game.match
        self.robot = robot

    def start(self):
        pass

    def decide(self):
        ball = self.match.ball
        robot = self.robot

        return to_point(
            [ball.x, ball.y],
            [robot.x, robot.y]
        )