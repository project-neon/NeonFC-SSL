"""DrunkWalk detour vectors.

np.array(r*cos(a), r*sin(a)) passes the second argument as `dtype`, not
as a second component -- every detour came back as a scalar on the
diagonal, so the "detour" was always straight ahead.
"""

import numpy as np

from neonfc_ssl.path_planning.drunk_walk.drunk_walk import DrunkWalk


def _drunk_walk():
    # The detour generators only need _step_vector and min_angle; the
    # full constructor wants a field, obstacles and walls.
    walker = DrunkWalk.__new__(DrunkWalk)
    walker._step_vector = np.array([1.0, 0.0])
    walker.min_angle = 0.1
    return walker


def test_random_detours_are_vectors():
    sub_dests = _drunk_walk()._gen_rnd_subdests()

    assert len(sub_dests) == 10
    for dest in sub_dests:
        assert isinstance(dest, np.ndarray)
        assert dest.shape == (2,)


def test_random_detours_point_in_different_directions():
    sub_dests = _drunk_walk()._gen_rnd_subdests()

    angles = {round(float(np.arctan2(d[1], d[0])), 3) for d in sub_dests}
    assert len(angles) > 1


def test_static_detours_are_vectors():
    sub_dests = _drunk_walk()._gen_static_subdests()

    assert len(sub_dests) == 10
    for dest in sub_dests:
        assert dest.shape == (2,)


def test_static_detours_point_in_different_directions():
    sub_dests = _drunk_walk()._gen_static_subdests()

    angles = {round(float(np.arctan2(d[1], d[0])), 3) for d in sub_dests}
    assert len(angles) > 1
