from neonfc_ssl.coach.coach import BaseCoach
from neonfc_ssl.coach.test_coach import Coach as TestCoach

_coach_list = [
    # Tournament coaches
    TestCoach
]

COACHES = {c.NAME: c for c in _coach_list}
