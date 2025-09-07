import pytest
from unittest.mock import MagicMock
from neonfc_ssl.decision_layer import utils


@pytest.mark.unit
def test_find_bracket_found():
    f = lambda x: x - 2
    bracket = utils.find_bracket(f, d_start=0, d_max=5)
    assert bracket[0] < 2 < bracket[1]


@pytest.mark.unit
def test_find_bracket_not_found():
    f = lambda x: x ** 2 + 1
    bracket = utils.find_bracket(f, d_start=0, d_max=5)
    assert bracket is None


@pytest.mark.unit
def test_interception_function():
    robot = MagicMock()
    ball = MagicMock()
    ball.tb.return_value = 5
    robot.time_to_target.return_value = 3
    ball.distance_to_vector.return_value = 1

    interception = utils.interception_function(robot, ball)
    result = interception(0)
    assert result == 2
    ball.tb.assert_called_with(0)
    robot.time_to_target.assert_called()


@pytest.mark.unit
def test_interception_distance_with_bracket():
    ball = MagicMock()
    ball.distance_to_vector.return_value = 42
    interception = lambda d: d - 1
    bracket = (0, 2)
    result = utils.interception_distance(ball, bracket, interception)
    assert result == 42
    ball.distance_to_vector.assert_called()


@pytest.mark.unit
def test_interception_distance_without_bracket():
    ball = MagicMock()
    ball.distance_to_vector.return_value = 0
    interception = MagicMock()
    bracket = None
    result = utils.interception_distance(ball, bracket, interception)
    assert result == 0
    ball.distance_to_vector.assert_called_with(0)


@pytest.mark.unit
def test_find_first_interception(monkeypatch):
    robot = MagicMock()
    ball = MagicMock()
    ball.tb.return_value = 5
    robot.time_to_target.return_value = 3
    ball.distance_to_vector.return_value = 1

    monkeypatch.setattr(utils, "find_bracket", lambda f: (0, 2))
    monkeypatch.setattr(utils, "interception_distance", lambda ball, bracket, interception: 7)

    result = utils.find_first_interception(robot, ball)
    assert result == 7
