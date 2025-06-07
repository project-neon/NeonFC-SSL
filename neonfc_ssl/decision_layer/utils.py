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


def find_first_interception(robot, ball):
    def rooted_interception(d):
        return ball.tb(d) - robot.time_to_target(ball.distance_to_vector(d))

    bracket = find_bracket(rooted_interception)
    if bracket:
        return ball.distance_to_vector(root_scalar(rooted_interception, bracket=bracket, xtol=0.5, method="brentq").root)

    else:
        return ball.distance_to_vector(0)
