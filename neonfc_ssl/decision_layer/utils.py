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
    func = lambda d: ball.tb(d) - robot.tr(ball.distance_to_vector(d))
    bracket = find_bracket(func)

    return ball.distance_to_vector(root_scalar(func, bracket=bracket, xtol=0.5, method="brentq").root)

