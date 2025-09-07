import pytest
import math
import numpy as np
from neonfc_ssl.tracking_layer.tracking_data import TrackedRobot, TrackedBall

@pytest.mark.unit
def test_trackedball_update_speed_and_v_shoot():
    ball = TrackedBall(x=1, y=2, vx=3, vy=4)
    assert np.isclose(ball.speed, 5.0)
    assert np.allclose(ball.v_shoot, [3, 4])
    assert isinstance(ball.v_switch, float)
    assert isinstance(ball.d_switch, float)

@pytest.mark.unit
def test_trackedball_distance_to_vector():
    ball = TrackedBall(x=1, y=2, vx=3, vy=4)
    pos = ball.distance_to_vector(1)
    assert isinstance(pos, np.ndarray)
    assert pos.shape == (2,)

@pytest.mark.unit
def test_trackedball_distance_to_vector_zero_velocity():
    ball = TrackedBall(x=1, y=2, vx=0, vy=0)
    pos = ball.distance_to_vector(1)
    assert isinstance(pos, np.ndarray)
    assert pos.shape == (2,)

@pytest.mark.unit
def test_tb_high_speed_switch():
    # Speed above v_switch, d < d_switch (sliding regime)
    ball = TrackedBall(x=0, y=0, vx=5, vy=0)
    d = 0.1
    t = ball.tb(d)
    assert t >= 0

@pytest.mark.unit
def test_tb_high_speed_past_switch():
    # Speed above v_switch, d > d_switch (slide then roll)
    ball = TrackedBall(x=0, y=0, vx=5, vy=0)
    d = ball.d_switch + 0.1
    t = ball.tb(d)
    assert t >= 0

@pytest.mark.unit
def test_tb_low_speed():
    # Speed below v_switch (rolling regime)
    ball = TrackedBall(x=0, y=0, vx=0.1, vy=0)
    d = 0.01
    t = ball.tb(d)
    assert t >= 0

@pytest.mark.unit
def test_tb_distance_too_large():
    # Distance too large to reach, should return math.inf
    ball = TrackedBall(x=0, y=0, vx=1, vy=0)
    d = 1e6
    t = ball.tb(d)
    assert t == math.inf
