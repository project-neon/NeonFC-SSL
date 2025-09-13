import numpy as np
from math import cos, sin, atan2, asin, pi
from typing import List, Tuple, Optional
from enum import Enum
from .vo_data import Obstacle, Cone
from neonfc_ssl.commons.math import is_angle_between, length
from neonfc_ssl.commons.math import distance_between_points as distance


class VOType(Enum):
    VO = "vo"
    RVO = "rvo"
    HRVO = "hrvo"


class StarVO:
    def __init__(self, pos: Tuple[float, float], goal: Tuple[float, float],
                 vel: Tuple[float, float], max_vel: float = 2.0, radius: float = 0.09,
                 priority: int = 0, goal_tolerance: float = 0.05,
                 safety_margin: float = 0.05, vo_type: VOType = VOType.HRVO):

        self.pos = np.array(pos, dtype=np.float64)
        self.goal = np.array(goal, dtype=np.float64)
        self.v = np.array(vel, dtype=np.float64)
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

        # Computed values
        self.desired_v = self._compute_desired_velocity()
        self.collision_cones: List[Cone] = []

        # Parameters
        self.angular_resolution = 0.1
        self.velocity_samples = 5
        self.max_neighbor_distance = 1.0
        self.min_safe_ttc = 0.5

    def _filter_obstacles(self, obstacles: List[Tuple]):
        """Obstacles spatial filtering"""
        filtered_obs = []

        for o in obstacles:
            pos = np.array(o[0])

            if distance(pos, self.pos) < self.max_neighbor_distance:
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
        """Update walls with spatial filtering and treat them as static obstacles"""
        filtered_walls = []

        for w in walls:
            start, end = np.array(w[0]), np.array(w[1])

            wall_vec = end - start
            to_agent = self.pos - start

            t = np.dot(to_agent, wall_vec) / np.dot(wall_vec, wall_vec)
            t_clamped = max(0, min(1, t))
            closest_point = start + t_clamped * wall_vec

            if length(closest_point - self.pos) < self.max_neighbor_distance:
                filtered_walls.append([closest_point, np.zeros(2), 0, 0])

        self.update_static_obstacles(filtered_walls)

    def reached_goal(self) -> bool:
        """Check if agent reached goal"""
        return distance(self.pos, self.goal) < self.goal_tolerance

    def _compute_desired_velocity(self) -> np.ndarray:
        """Compute desired velocity with speed limiting"""
        if self.reached_goal():
            return np.array([1e-6, 1e-6])

        goal_vec = self.goal - self.pos
        goal_dist = length(goal_vec)

        return (goal_vec / goal_dist) * self.max_v

    @staticmethod
    def _handle_center_case(desired_v: np.ndarray) -> Tuple[float, float]:
        """Handle the special case when agent is exactly at obstacle center"""
        if np.linalg.norm(desired_v) > 1e-6:
            theta_center = atan2(desired_v[1], desired_v[0])
        else:
            theta_center = 0
        theta_half = pi / 4  # Wide emergency cone
        return theta_center, theta_half

    @staticmethod
    def _handle_near_edge_case(rel_pos: np.ndarray) -> Tuple[float, float]:
        """Handle case when agent is near the edge of the obstacle"""
        theta_center = atan2(rel_pos[1], rel_pos[0])
        # For very close obstacles, use maximum half-angle
        theta_half = pi / 2 - 1e-3  # Nearly full cone but avoid numerical issues
        return theta_center, theta_half

    @staticmethod
    def _handle_normal_case(rel_pos: np.ndarray, dist: float, combined_radius: float) -> Tuple[float, float]:
        """Handle normal case where agent is outside the obstacle"""
        theta_center = atan2(rel_pos[1], rel_pos[0])
        # Safe division - dist > combined_radius guaranteed here
        sin_theta_half = min(combined_radius / dist, 1.0)
        theta_half = asin(sin_theta_half)
        return theta_center, theta_half

    def _calculate_cone_base(self, obs_vel: np.ndarray, obs_priority: int, is_dynamic: bool) -> np.ndarray:
        """Calculate the base point (apex) of the cone"""
        if not is_dynamic:
            return self.pos + obs_vel

        if self.vo_type == "HRVO":
            if self.priority > obs_priority:
                return self.pos + obs_vel
            else:
                return self.pos + 0.5 * (self.v + obs_vel)
        elif self.vo_type == "RVO":
            return self.pos + 0.5 * (self.v + obs_vel)
        else:
            return self.pos + obs_vel

    def _compute_collision_cone(self, obs_pos: np.ndarray, obs_vel: np.ndarray,
                              obs_radius: float, obs_priority: int = 0,
                              is_dynamic: bool = True) -> Optional[Cone]:
        """Cone computation with improved numerical stability"""
        rel_pos = obs_pos - self.pos
        dist = length(rel_pos) + 1e-6

        combined_radius = self.effective_radius + obs_radius

        # Handle case where agent is inside or very close to obstacle
        if dist <= combined_radius:
            # Agent is inside or touching the obstacle
            if dist < 1e-6:
                theta_center, theta_half = self._handle_center_case(self.desired_v)
            else:
                theta_center, theta_half = self._handle_near_edge_case(rel_pos)
        else:
            theta_center, theta_half = self._handle_normal_case(rel_pos, dist, combined_radius)

        left_angle = (theta_center + theta_half) % (2*pi)
        right_angle = (theta_center - theta_half) % (2*pi)

        # Calculate cone base
        base = self._calculate_cone_base(obs_vel, obs_priority, is_dynamic)

        return Cone(base, dist, combined_radius, left_angle, right_angle)

    def _is_velocity_safe(self, velocity: np.ndarray) -> bool:
        """Check if given velocity might generate a collision"""
        vel_mag_sq = np.dot(velocity, velocity)

        if vel_mag_sq > self.max_v * self.max_v:
            return False

        # Check cones
        for cone in self.collision_cones:
            vec = self.pos + velocity - cone.base
            vec_mag_sq = np.dot(vec, vec)
            if vec_mag_sq < 1e-12:
                return False

            angle = atan2(vec[1], vec[0])
            if is_angle_between(angle, cone.right_angle, cone.left_angle):
                return False

        return True

    def _generate_candidate_velocities(self, base_angle: float) -> tuple:
        suitable_v = []
        unsuitable_v = []
        for theta in np.linspace(-2 * pi / 3, 2 * pi / 3 + 0.05, 21):
            angle = base_angle + theta
            direction = np.array([cos(angle), sin(angle)])
            for speed in np.linspace(1e-6, self.max_v, self.velocity_samples + 1):
                candidate = direction * speed
                if self._is_velocity_safe(candidate):
                    suitable_v.append(candidate)
                else:
                    unsuitable_v.append(candidate)
        return suitable_v, unsuitable_v

    def _calculate_ttc_for_velocities(self, velocities: list) -> dict:
        tc_v = {}
        for v in velocities:
            tc_v[tuple(v)] = self._calculate_single_velocity_ttc(v)
        return tc_v

    def _calculate_single_velocity_ttc(self, v: np.ndarray) -> float:
        tc = []
        for cone in self.collision_cones:
            ttc_val = self._calculate_cone_ttc(v, cone)
            if ttc_val is not None:
                tc.append(ttc_val)
        return max(min(tc), 1e-6) if tc else 1e-6

    def _calculate_cone_ttc(self, v: np.ndarray, cone) -> float:
        vec = self.pos + v - cone.base
        vec_mag = length(vec)
        if vec_mag < 1e-12:
            return 0.0

        theta = atan2(vec[1], vec[0])
        if not is_angle_between(theta, cone.right_angle, cone.left_angle):
            return 0.0

        rad = cone.radius
        small_theta = abs(theta - 0.5 * (cone.left_angle + cone.right_angle))
        if abs(cone.dist * sin(small_theta)) >= rad:
            rad = abs(cone.dist * sin(small_theta))

        big_theta = asin(min(abs(cone.dist * sin(small_theta)) / rad, 1.0))
        dist_tg = abs(cone.dist * cos(small_theta)) - abs(rad * cos(big_theta))
        dist_tg = max(dist_tg, 0)
        return dist_tg / vec_mag if vec_mag > 1e-12 else 0.0

    def _select_fallback_velocity(self, velocities: list, tc_v: dict, desired_v: np.ndarray) -> np.ndarray:
        WT = 0.2
        best_v = min(velocities, key=lambda vel: (WT / tc_v[tuple(vel)]) + distance(vel, desired_v))
        return np.array([1e-6, 1e-6]) if tc_v[tuple(best_v)] < self.min_safe_ttc else best_v

    def _find_best_velocity(self) -> np.ndarray:
        if self._is_velocity_safe(self.desired_v):
            return self.desired_v

        base_angle = atan2(self.desired_v[1], self.desired_v[0])
        suitable_v, unsuitable_v = self._generate_candidate_velocities(base_angle)

        if suitable_v:
            return min(suitable_v, key=lambda vel: distance(vel, self.desired_v))

        if not unsuitable_v:
            return np.zeros(2)

        tc_v = self._calculate_ttc_for_velocities(unsuitable_v)
        return self._select_fallback_velocity(unsuitable_v, tc_v, self.desired_v)

    def update(self) -> np.ndarray:
        """
        Returns:
            Selected velocity vector
        """
        self.desired_v = self._compute_desired_velocity()

        self.collision_cones = []

        for obs in self.dynamic_obstacles:
            cone = self._compute_collision_cone(obs.pos, obs.vel, obs.radius,
                                             obs.priority, is_dynamic=True)
            if cone is not None:
                self.collision_cones.append(cone)

        for obs in self.static_obstacles:
            cone = self._compute_collision_cone(obs.pos, obs.vel, obs.radius,
                                             obs.priority, is_dynamic=False)
            if cone is not None:
                self.collision_cones.append(cone)

        selected_velocity = self._find_best_velocity()

        return selected_velocity
