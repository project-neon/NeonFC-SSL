"""Action -> RobotRubric mapping.

The raw tanh output was used directly as the target heading, capping the
robot's orientation at +-1 radian: it could never be told to face up the
field.
"""

import math

import pytest
import torch

from neonfc_ssl.decision_layer.drl.transformations.output_1_v_1 import (
    one_v_one_output_transformation,
)


class _Field:
    field_length = 9.0
    field_width = 6.0


class _MatchData:
    field = _Field()


@pytest.mark.parametrize(
    "theta_action, expected",
    [(1.0, math.pi), (-1.0, -math.pi), (0.5, math.pi / 2), (-0.5, -math.pi / 2), (0.0, 0.0)],
)
def test_theta_spans_the_full_circle(theta_action, expected):
    actions = {
        "goalkeeper": torch.tensor([0.0, 0.0, theta_action, 0.0]),
        "striker": torch.tensor([0.0, 0.0, theta_action, 0.0]),
    }

    rubrics = one_v_one_output_transformation(actions, _MatchData())

    for rubric in rubrics.values():
        assert rubric.target_pose[2] == pytest.approx(expected)


def test_xy_rescaling_is_unchanged():
    actions = {
        "goalkeeper": torch.tensor([-1.0, 1.0, 0.0, 0.0]),
        "striker": torch.tensor([-1.0, 1.0, 0.0, 0.0]),
    }

    rubrics = one_v_one_output_transformation(actions, _MatchData())

    for rubric in rubrics.values():
        assert rubric.target_pose[0] == pytest.approx(0.0)
        assert rubric.target_pose[1] == pytest.approx(6.0)


def test_kick_threshold_is_unchanged():
    actions = {
        "goalkeeper": torch.tensor([0.0, 0.0, 0.0, 0.6]),
        "striker": torch.tensor([0.0, 0.0, 0.0, 0.4]),
    }

    rubrics = one_v_one_output_transformation(actions, _MatchData())

    assert rubrics[0].kick_speed[0] > 0.0
    assert rubrics[1].kick_speed[0] == 0.0
