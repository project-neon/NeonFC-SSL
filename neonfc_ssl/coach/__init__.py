from neonfc_ssl.coach.coach import BaseCoach
from neonfc_ssl.coach.test_coach import Coach as TestCoach
from neonfc_ssl.coach.simple_coach import Coach as SimpleCoach

_coach_list = [
    # Tournament coaches
    TestCoach,
    SimpleCoach
]

COACHES = {c.NAME: c for c in _coach_list}
