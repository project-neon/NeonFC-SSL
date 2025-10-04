import numpy as np
from itertools import product
from math import cos, sin, atan2, asin, pi
from typing import List, Tuple, Iterator, Any
from .vo_data import VOType, Obstacle, Cone
from neonfc_ssl.commons.math import is_angle_between, length
from neonfc_ssl.commons.math import distance_between_points as distance


class StarVO:
    def __init__(self, pos: Tuple[float, float], goal: Tuple[float, float],
                 vel: Tuple[float, float], max_vel: float = 2.0, radius: float = 0.09,
                 priority: int = 0, goal_tolerance: float = 0.05,
                 safety_margin: float = 0.05, vo_type: VOType = VOType.HRVO):

        self.pos = np.array(pos, dtype=np.float64)
        self.goal = np.array(goal, dtype=np.float64)
        self.vel = np.array(vel, dtype=np.float64)
        self.max_vel = max_vel
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
        self.angular_samples = 21
        self.velocity_samples = 5
        self.max_neighbor_distance = 1.0
        self.min_wall_dist = 0.1

    def _filter_obstacles(self, obstacles: List[Tuple]|Iterator[Any]):
        """Obstacles spatial filtering"""

        obstacles = map(lambda obs: Obstacle(*obs), obstacles)

        return list(filter(
            lambda obs: distance(obs.pos, self.pos) < self.max_neighbor_distance,
            obstacles
        ))

    def update_static_obstacles(self, static_obstacles: List[Tuple]):
        """Update static obstacles"""

        self.static_obstacles = self._filter_obstacles(static_obstacles)

    def update_dynamic_obstacles(self, dynamic_obstacles: List[Tuple]):
        """Update dynamic obstacles"""

        self.dynamic_obstacles = self._filter_obstacles(dynamic_obstacles)

    def _process_wall(self, wall):
        start, end = np.array(wall[0]), np.array(wall[1])
        wall_vec = end - start
        to_agent = self.pos - start

        if length(wall_vec) < 1e-6:
            return None

        t = np.dot(to_agent, wall_vec) / np.dot(wall_vec, wall_vec)
        t_clamped = max(0, min(1, t))
        closest_point = start + t_clamped * wall_vec

        wall_obstacle = [closest_point, np.zeros(2), self.min_wall_dist]
        return wall_obstacle

    def update_walls(self, walls: List[Tuple]):
        """Update walls with spatial filtering and treat them as static obstacles"""
        walls = filter(None, map(self._process_wall, walls))
        filtered_walls = self._filter_obstacles(walls)

        self.static_obstacles.extend(filtered_walls)

    def reached_goal(self) -> bool:
        """Check if agent reached goal"""
        return distance(self.pos, self.goal) < self.goal_tolerance

    def _compute_desired_velocity(self) -> np.ndarray:
        """Compute desired velocity with speed limiting"""
        if self.reached_goal():
            return np.array([0, 0])

        goal_vec = self.goal - self.pos
        goal_dist = length(goal_vec)

        return (goal_vec / goal_dist) * self.max_vel

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

        if self.vo_type == VOType.HRVO:
            if self.priority > obs_priority:
                return self.pos + obs_vel
            else:
                return self.pos + 0.5 * (self.vel + obs_vel)
        elif self.vo_type == VOType.RVO:
            return self.pos + 0.5 * (self.vel + obs_vel)
        else:
            return self.pos + obs_vel

    def _compute_collision_cone(self, obs_pos: np.ndarray, obs_vel: np.ndarray,
                              obs_radius: float, obs_priority: int = 0,
                              is_dynamic: bool = True) -> Cone:
        """Cone computation with improved numerical stability"""
        rel_pos = obs_pos - self.pos
        dist = length(rel_pos)

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

        if vel_mag_sq > self.max_vel * self.max_vel + 1e-6:
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

    @staticmethod
    def _create_candidate(base_angle: float, theta: float, velocity: float):
        return velocity * np.array([cos(base_angle + theta), sin(base_angle + theta)])

    def _generate_candidate_velocities(self, base_angle: float) -> List:
        angles = np.linspace(-pi / 4, pi / 4 + 0.05, self.angular_samples)
        velocities = np.linspace(1e-6, self.max_vel, self.velocity_samples + 1)

        candidates = [
            self._create_candidate(base_angle, theta, vel)
            for theta, vel in product(angles, velocities)
        ]

        return list(filter(self._is_velocity_safe, candidates))

    def _find_best_velocity(self) -> np.ndarray:
        if self._is_velocity_safe(self.desired_v):
            return self.desired_v

        base_angle = atan2(self.desired_v[1], self.desired_v[0])
        suitable_v = self._generate_candidate_velocities(base_angle)

        return min(suitable_v, key=lambda vel: distance(vel, self.desired_v), default=np.zeros(2))

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
