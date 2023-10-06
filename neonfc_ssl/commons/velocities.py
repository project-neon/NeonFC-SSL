from math import pi


def _fix_angle(theta_1, theta_2):
    rate_theta = (theta_2 - theta_1)
  
    if (rate_theta > pi ):
        rate_theta -= 2 * pi
    elif (rate_theta < -pi):
        rate_theta += 2 * pi

    return rate_theta

def avg_angular_speed(_list, _fps):
    if len(_list) <= 1:
        return 0
    
    speed_fbf = [
        _fix_angle(t0, t1) for t0, t1 
        in zip(
            _list, 
            list(_list)[1:]
        )
    ]
    if not speed_fbf:
        return 0
    return _fps * (sum(speed_fbf)/len(speed_fbf))

def avg_linear_speed(_list, _fps):
    if len(_list) <= 1:
        return 0
    
    speed_fbf = [
        (t1 - t0) for t0, t1 
        in zip(
            _list, 
            list(_list)[1:]
        ) if abs((t1 - t0)) < 0.1
        # considering the game runs at 60 fps
        # to limit 0.1 m/f here is to say that is impossible
        # for the robot to run at 6 m/s (0.1 [m][f⁻¹] * 60 [f][s⁻¹] = 6[m][s⁻¹])
    ]
    if not speed_fbf:
        return 0
    return _fps * (sum(speed_fbf)/len(speed_fbf))