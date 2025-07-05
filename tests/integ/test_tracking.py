import pytest
from .fixture import *
from neonfc_ssl.tracking_layer import Tracking
from neonfc_ssl.input_layer import data as input_data
from neonfc_ssl.tracking_layer import data as tracking_data


@pytest.mark.integration
def test_tracking_layer(base_config):
    layer_obj, pipe_in, pipe_out, log_q = instance_layer(Tracking, base_config)

    ids = [0]

    test_data = input_data.InputData(
        entities=input_data.Entities(
            ball=input_data.Ball(x=0, y=0, vx=0, vy=0),
            robots_blue={r_id: input_data.Robot(id=r_id, team='blue', x=0, y=0, theta=0, vx=0, vy=0, vtheta=0) for r_id in ids},
            robots_yellow={r_id: input_data.Robot(id=r_id, team='yellow', x=0, y=0, theta=0, vx=0, vy=0, vtheta=0) for r_id in ids},
        ),
        geometry=input_data.Geometry(0, 0, 0, 0, 0),
        game_controller=input_data.GameController(True, "", (0, 0), 'blue'),
    )

    layer_obj.start()

    pipe_in.send(test_data)

    response:tracking_data.MatchData = pipe_out.recv()

    assert isinstance(response, tracking_data.MatchData), "Wrong return type"

    assert len(response.robots.actives) == len(ids)
    assert len(response.robots.robots) == 16

    assert len(response.opposites.actives) == len(ids)
    assert len(response.opposites.robots) == 16
