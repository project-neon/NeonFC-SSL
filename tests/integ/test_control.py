import pytest
import numpy as np
from .fixture import *
from neonfc_ssl.control_layer import Control
from neonfc_ssl.control_layer import control_data
from neonfc_ssl.tracking_layer import tracking_data
from neonfc_ssl.decision_layer import decision_data

@pytest.mark.integration
def test_control_layer(base_config):
    layer_obj, pipe_in, pipe_out, log_q = instance_layer(Control, base_config)

    ids = [0]

    test_data = decision_data.DecisionData(
        commands=[decision_data.RobotRubric(id=r_id, halt=False, target_pose=(1, 1, 0), avoid_area=True, avoid_opponents=ids) for r_id in ids],
        world_model=tracking_data.MatchData(
            ball=tracking_data.TrackedBall(
                x=0.0, y=0.0, z=None, vx=0, vy=0, vz=None,
            ),
            possession=tracking_data.Possession(
                my_closest=0, op_closest=0, possession_balance=np.float64(0.0),
                contact_start_position=np.array([0., 0.])
            ),
            game_state=tracking_data.GameState(
                state=tracking_data.States.HALT, color=None, friendly=False, position=None
            ),
            field=tracking_data.Geometry(
                field_length=0, field_width=0, goal_width=0, penalty_depth=0, penalty_width=0
            ),
            robots=tracking_data.RobotList(
                robots=[tracking_data.TrackedRobot(id=r_id, color='yellow', x=0.0, y=0.0, theta=0, vx=0, vy=0, vtheta=0, missing=False) for r_id in ids],
            ),
            opposites=tracking_data.RobotList(
                robots=[tracking_data.TrackedRobot(id=r_id, color='blue', x=0.0, y=0.0, theta=0, vx=0, vy=0, vtheta=0, missing=False) for r_id in ids],
            ),
            is_yellow=True
        )
    )

    layer_obj.start()
    pipe_in.send(test_data)
    response = pipe_out.recv()

    assert isinstance(response, control_data.ControlData), "Response should be a ControlData instance"
    assert len(response.commands) == len(ids), "Number of commands should match number of ids"