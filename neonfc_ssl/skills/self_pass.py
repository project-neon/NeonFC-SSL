from neonfc_ssl.algorithms.fsm import State
from neonfc_ssl.skills.base_skill import BaseSkill
from neonfc_ssl.entities import RobotCommand
from neonfc_ssl.commons.math import reduce_ang
import math


class SelfPass(BaseSkill):
    def __init__(self, coach, match):
        super().__init__('Pass', coach, match)

    def decide(self):
        pass
