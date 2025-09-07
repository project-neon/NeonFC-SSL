from scipy.optimize import root_scalar


def find_bracket(f, *params, d_start=0.0, d_max=10.0, step=0.05):
    d_left = d_start
    f_left = f(d_left, *params)

    d = d_left + step
    while d <= d_max:
        f_right = f(d, *params)
        if f_left * f_right < 0:
            return d_left, d  # Found bracket
        d_left = d
        f_left = f_right
        d += step

    return None


def interception_function(robot, ball):
    def rooted_interception(d):
        return ball.tb(d) - robot.time_to_target(ball.distance_to_vector(d))
    return rooted_interception


def interception_distance(ball, bracket, interception):
    if bracket:
        return ball.distance_to_vector(root_scalar(interception, bracket=bracket, xtol=0.5, method="brentq").root)
    else:
        return ball.distance_to_vector(0)


def find_first_interception(robot, ball):
    interception = interception_function(robot, ball)
    bracket = find_bracket(interception)
    return interception_distance(ball, bracket, interception)
