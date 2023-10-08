import numpy as np

from algorithms.potential_fields.fields import PointField

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

class GoalKeeper():
    def __init__(self, robot):
        self.name = 'GOALKEEPER'
        self.match = robot.game.match
        self.robot = robot
        
        self.goal_right = -500
        self.goal_left = 500

    def start(self):
        def proj(m):
            projection_rate = -(m.ball.x-.15)/(1-.15)
            projection_point = m.ball.y + projection_rate * m.ball.vy

            y = min(
                max(projection_point, self.goal_right), 
                self.goal_left
            )

            return -4450, y

        self.to_ball = PointField(
                self.match,
                target = proj,
                radius = 0.45,
                multiplier = 1,
                decay = lambda x : 0 if x < 0.5 else x
            )

    def decide(self):
        return self.to_ball.compute([self.robot.x, self.robot.y])