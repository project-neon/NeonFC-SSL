import numpy as np
from math import cos, sin, atan2, asin, pi, sqrt
from typing import List, Tuple, Optional
from enum import Enum
from .vo_data import Obstacle, Wall, Cone

class VOType(Enum):
    VO = "vo"
    RVO = "rvo"
    HRVO = "hrvo"


class StarVO:
    def __init__(self, pos: Tuple[float, float], goal: Tuple[float, float],
                 vel: Tuple[float, float], max_vel: float, radius: float,
                 priority: int = 0, goal_tolerance: float = 0.1,
                 safety_margin: float = 0.05, vo_type: VOType = VOType.HRVO):

        self.pos = np.array(pos, dtype=np.float32)
        self.goal = np.array(goal, dtype=np.float32)
        self.v = np.array(vel, dtype=np.float32)
        self.max_v = max_vel
        self.radius = radius
        self.priority = priority
        self.goal_tolerance = goal_tolerance
        self.safety_margin = safety_margin
        self.effective_radius = radius + safety_margin
        self.vo_type = vo_type

        # Environment
        self.static_obstacles: List[Obstacle] = []
        self.dynamic_obstacles: List[Obstacle] = []
        self.walls: List[Wall] = []

        # Computed values
        self.desired_v = self._compute_desired_velocity()
        self.collision_cones: List[Cone] = []

        # Parameters
        self.angular_resolution = 0.1
        self.velocity_samples = 5
        self.time_horizon = 2.0
        self.max_neighbor_distance = 1.0

    def _filter_obstacles(self, obstacles: List[Tuple]):
        """Obstacles spatial filtering"""
        filtered_obs = []

        for o in obstacles:
            pos = np.array(o[0])
            dist = self.distance(pos, self.pos)

            if dist < self.max_neighbor_distance:
                filtered_obs.append(
                    Obstacle(pos, np.array(o[1]), o[2], o[3] if len(o) > 3 else 0)
                )

        return filtered_obs

    def update_static_obstacles(self, static_obstacles: List[Tuple]):
        """Update static obstacles"""

        self.static_obstacles = self._filter_obstacles(static_obstacles)

    def update_dynamic_obstacles(self, dynamic_obstacles: List[Tuple]):
        """Update dynamic obstacles"""

        self.dynamic_obstacles = self._filter_obstacles(dynamic_obstacles)

    def update_walls(self, walls: List[Tuple]):
        """Update walls with spatial filtering"""
        filtered_walls = []

        for w in walls:
            start, end = np.array(w[0]), np.array(w[1])

            wall_vec = end - start
            to_agent = self.pos - start

            t = np.dot(to_agent, wall_vec) / np.dot(wall_vec, wall_vec)
            t_clamped = max(0, min(1, t))
            closest_point = start + t_clamped * wall_vec

            if np.linalg.norm(closest_point - self.pos) < self.max_neighbor_distance:
                filtered_walls.append(Wall(start, end))

        self.walls = filtered_walls

    @staticmethod
    def distance(a: np.ndarray, b: np.ndarray = None) -> float:
        if b is None:
            b = np.zeros(2)
        return np.linalg.norm(a - b) + 1e-6

    def reached_goal(self) -> bool:
        """Check if agent reached goal"""
        return self.distance(self.pos, self.goal) < self.goal_tolerance

    def _compute_desired_velocity(self) -> np.ndarray:
        """Compute desired velocity with speed limiting"""
        if self.reached_goal():
            return np.array([1e-6, 1e-6])

        goal_vec = self.goal - self.pos
        goal_dist = np.linalg.norm(goal_vec)

        if goal_dist < 1e-6:
            return np.array([1e-6, 1e-6])

        return (goal_vec / goal_dist) * self.max_v

    @staticmethod
    def _is_angle_between(angle: float, start: float, end: float) -> bool:
        angle = angle % (2*pi)
        start = start % (2*pi)
        end = end % (2*pi)

        if start <= end:
            return start <= angle <= end
        else:
            return angle >= start or angle <= end

    def _compute_rvo_cone(self, obs_pos: np.ndarray, obs_vel: np.ndarray,
                              obs_radius: float, obs_priority: int = 0,
                              is_dynamic: bool = True) -> Optional[Cone]:
        """Cone computation with improved numerical stability"""
        rel_pos = obs_pos - self.pos
        dist = np.linalg.norm(rel_pos) + 1e-6

        combined_radius = self.effective_radius + obs_radius

        # Early exit for distant obstacles
        max_influence_dist = self.time_horizon * (self.max_v + np.linalg.norm(obs_vel))
        if dist > max_influence_dist:
            return None

        # Handle case where agent is inside or very close to obstacle
        if dist <= combined_radius:
            # Agent is inside or touching the obstacle
            if dist < 1e-6:
                # Agent exactly at obstacle center - create emergency cone
                theta_center = atan2(self.desired_v[1], self.desired_v[0]) if np.linalg.norm(self.desired_v) > 1e-6 else 0
                theta_half = pi/4  # Wide emergency cone
            else:
                theta_center = atan2(rel_pos[1], rel_pos[0])
                # For very close obstacles, use maximum half-angle
                theta_half = pi/2 - 1e-3  # Nearly full cone but avoid numerical issues
        else:
            theta_center = atan2(rel_pos[1], rel_pos[0])
            # Safe division - dist > combined_radius guaranteed here
            sin_theta_half = min(combined_radius / dist, 1.0)
            theta_half = asin(sin_theta_half)

        left_angle = (theta_center + theta_half) % (2*pi)
        right_angle = (theta_center - theta_half) % (2*pi)

        if is_dynamic and self.vo_type == VOType.HRVO:
            if self.priority > obs_priority:
                base = self.pos + obs_vel
            else:
                base = self.pos + 0.5 * (self.v + obs_vel)
        elif is_dynamic and self.vo_type == VOType.RVO:
            base = self.pos + 0.5 * (self.v + obs_vel)
        else:
            base = self.pos + obs_vel

        return Cone(base, dist, combined_radius, left_angle, right_angle)

    @staticmethod
    def _solve_quadratic(a: float, b: float, c: float,
                         max_time: float = float('inf')) -> float:
        """
        Solves quadratic equation a*t^2 + b*t + c = 0.
        Returns smallest non-negative real root <= max_time, or inf if none exists.
        """
        # Handle linear case
        if abs(a) < 1e-12:
            if abs(b) < 1e-12:
                return float('inf')
            t = -c / b
            return t if 0 <= t <= max_time else float('inf')

        # Quadratic case
        discriminant = b*b - 4*a*c
        if discriminant < 0:
            return float('inf')

        sqrt_d = sqrt(discriminant)
        denom = 2*a

        # Numerically stable roots
        if b >= 0:
            root1 = (-b - sqrt_d) / denom
            root2 = 2*c / (-b - sqrt_d) if abs(b + sqrt_d) > 1e-12 else float('inf')
        else:
            root1 = 2*c / (-b + sqrt_d) if abs(-b + sqrt_d) > 1e-12 else float('inf')
            root2 = (-b + sqrt_d) / denom

        # Find smallest non-negative root within time horizon
        valid_roots = []
        for root in (root1, root2):
            if not (np.isnan(root) or np.isinf(root)) and 0 <= root <= max_time:
                valid_roots.append(root)

        return min(valid_roots) if valid_roots else float('inf')

    def _calculate_wall_ttc(self, agent_pos: np.ndarray,
                                    velocity: np.ndarray,
                                    wall_start: np.ndarray,
                                    wall_end: np.ndarray,
                                    agent_radius: float,
                                    time_horizon: float = float('inf')) -> float:
        """
        Calculates time to collision with wall using geometry

        Returns:
            Time to collision (inf if no collision within time_horizon)
        """
        A = wall_start
        B = wall_end
        P = agent_pos
        v = velocity
        r = agent_radius

        # Vector from wall start to end
        u = B - A
        u_sq = np.dot(u, u)

        # Vector from wall start to agent
        w0 = P - A

        # Check current collision
        if u_sq < 1e-12:  # Degenerate wall (point)
            dist_sq = np.dot(w0, w0)
            if dist_sq <= r*r:
                return 0.0
        else:
            # Compute closest point on segment
            t_val = np.dot(w0, u) / u_sq
            t_clamped = max(0, min(1, t_val))
            closest_point = A + t_clamped * u
            dist_sq = np.dot(P - closest_point, P - closest_point)
            if dist_sq <= r*r:
                return 0.0

        # For stationary agent, only current collision matters
        v_sq = np.dot(v, v)

        if v_sq < 1e-12:
            return float('inf')

        # For degenerate wall (point)
        if u_sq < 1e-12:
            # Solve: ||P + v*t - A|| = r
            a = v_sq
            b = 2 * np.dot(w0, v)
            c = np.dot(w0, w0) - r*r

            return self._solve_quadratic(a, b, c, time_horizon)

        # General case: moving circle vs line segment
        # We'll solve for three cases and take minimum valid t
        t_candidates = []

        # Case 1: Collision with infinite line
        # Equation: (w0 + v*t) × u / |u| = r (squared)
        u_norm_sq = u_sq
        cross_w0u = w0[0]*u[1] - w0[1]*u[0]
        cross_vu = v[0]*u[1] - v[1]*u[0]

        a1 = cross_vu*cross_vu
        b1 = 2 * cross_vu * cross_w0u
        c1 = cross_w0u*cross_w0u - r*r * u_norm_sq

        t1 = self._solve_quadratic(a1, b1, c1, time_horizon)
        if t1 < float('inf'):
            # Verify projection is on segment
            proj = np.dot(w0, u) + np.dot(v, u)*t1
            if 0 <= proj <= u_sq:
                t_candidates.append(t1)

        # Case 2: Collision with endpoint A
        a2 = v_sq
        b2 = 2 * np.dot(w0, v)
        c2 = np.dot(w0, w0) - r*r
        t2 = self._solve_quadratic(a2, b2, c2, time_horizon)
        if t2 < float('inf'):
            t_candidates.append(t2)

        # Case 3: Collision with endpoint B
        w1 = P - B
        a3 = v_sq
        b3 = 2 * np.dot(w1, v)
        c3 = np.dot(w1, w1) - r*r
        t3 = self._solve_quadratic(a3, b3, c3, time_horizon)
        if t3 < float('inf'):
            t_candidates.append(t3)

        return min(t_candidates) if t_candidates else float('inf')

    def _is_velocity_safe(self, velocity: np.ndarray) -> bool:
        """Optimized collision checking using analytical wall collision detection"""
        vel_mag_sq = np.dot(velocity, velocity)

        if vel_mag_sq > self.max_v * self.max_v + 1e-6:
            return False

        # Check cones
        for cone in self.collision_cones:
            if cone is None:
                continue

            vec = self.pos + velocity - cone.base
            vec_mag_sq = np.dot(vec, vec)
            if vec_mag_sq < 1e-12:
                return False

            angle = atan2(vec[1], vec[0])
            if self._is_angle_between(angle, cone.right_angle, cone.left_angle):
                return False

        # Check walls using analytical method
        for wall in self.walls:
            if self._calculate_wall_ttc(
                self.pos, velocity, wall.start, wall.end,
                self.effective_radius, self.time_horizon
            ) <= self.time_horizon:
                return False

        return True

    def _find_best_velocity(self) -> np.ndarray:
        if self._is_velocity_safe(self.desired_v):
            return self.desired_v

        suitable_v = []
        unsuitable_v = []

        base_angle = atan2(self.desired_v[1], self.desired_v[0])

        for theta in np.linspace(-2*pi/3, 2*pi/3 + 0.05, 21): # Theta range makes a lot of difference depending on the obstacle format
            angle = base_angle + theta
            direction = np.array([cos(angle), sin(angle)])
            for speed in np.linspace(1e-6, self.max_v, self.velocity_samples + 1):
                candidate = direction * speed

                if self._is_velocity_safe(candidate):
                    suitable_v.append(candidate)
                else:
                    unsuitable_v.append(candidate)

        if suitable_v:
            return min(suitable_v, key=lambda vel: self.distance(vel, self.desired_v))

        tc_v = dict()

        for v in unsuitable_v:
            tc_v[tuple(v)] = 1e-6
            tc = []

            # Calculate TTC for cones
            for cone in self.collision_cones:
                if cone is None:
                    continue

                vec = self.pos + v - cone.base
                vec_mag = np.linalg.norm(vec)
                if vec_mag < 1e-12:
                    tc.append(0.0)
                    continue

                theta = atan2(vec[1], vec[0])
                rad = cone.radius

                if self._is_angle_between(theta, cone.right_angle, cone.left_angle):
                    small_theta = abs(theta-0.5*(cone.left_angle+cone.right_angle))
                    if abs(cone.dist*sin(small_theta)) >= rad:
                        rad = abs(cone.dist*sin(small_theta))
                    big_theta = asin(min(abs(cone.dist*sin(small_theta))/rad, 1.0))
                    dist_tg = abs(cone.dist*cos(small_theta))-abs(rad*cos(big_theta))
                    if dist_tg < 0:
                        dist_tg = 0
                    ttc = (dist_tg/vec_mag) if vec_mag > 1e-12 else 0.0
                    tc.append(ttc)

            # Calculate TTC for walls
            for wall in self.walls:
                wall_ttc = self._calculate_wall_ttc(
                    self.pos, v, wall.start, wall.end, self.effective_radius, self.time_horizon
                )

                if wall_ttc < float('inf'):
                    tc.append(wall_ttc)

            if tc:
                tc_v[tuple(v)] = max(min(tc), 1e-6)  # Ensure minimum positive value

        if not tc_v:
            # No unsuitable velocities found, return zero velocity as emergency
            return np.zeros(2)

        WT = 0.2
        best_v = min(unsuitable_v, key=lambda vel: ((WT/tc_v[tuple(v)])+self.distance(vel, self.desired_v)))

        if tc_v[tuple(best_v)] < self.effective_radius:
            return np.array([1e-6, 1e-6])
        else:
            return best_v

    def update(self) -> np.ndarray:
        """
        Returns:
            Selected velocity vector
        """
        self.desired_v = self._compute_desired_velocity()

        self.collision_cones = []

        for obs in self.dynamic_obstacles:
            cone = self._compute_rvo_cone(obs.pos, obs.vel, obs.radius,
                                             obs.priority, is_dynamic=True)
            if cone is not None:
                self.collision_cones.append(cone)

        for obs in self.static_obstacles:
            cone = self._compute_rvo_cone(obs.pos, obs.vel, obs.radius,
                                             obs.priority, is_dynamic=False)
            if cone is not None:
                self.collision_cones.append(cone)

        selected_velocity = self._find_best_velocity()

        return selected_velocity.tolist()
