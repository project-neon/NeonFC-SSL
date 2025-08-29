import pytest
import numpy as np
from neonfc_ssl.control_layer.path_planning.base_planner import BasePathPlanner
from neonfc_ssl.control_layer.path_planning.rrt.rrt_planner import RRTPlanner, RRTStarPlanner


class PlannerTestConfig:
    """Configuration class for planner test parameters"""

    # Test scenarios
    SIMPLE_SCENARIO = {
        'start': (0.5, 0.5),
        'goal': (8.5, 5.5),
        'speed': (1.2, 0.8),
        'map_area': (9, 6),
        'obstacles': [(3, 3), (3, 4), (4, 3), (4, 4), (6, 4), (7, 4)]
    }

    NO_OBSTACLES_SCENARIO = {
        'start': (1, 1),
        'goal': (8, 5),
        'speed': (2.0, 1.5),
        'map_area': (9, 6),
        'obstacles': []
    }

    DENSE_OBSTACLES_SCENARIO = {
        'start': (1, 3),
        'goal': (8, 3),
        'speed': (0.8, 1.2),
        'map_area': (9, 6),
        'obstacles': [(x, y) for x in range(4, 6) for y in range(0, 7)]
    }


@pytest.fixture
def planner():
    return RRTStarPlanner(
        step_size=0.1,  # Moderate step size for balanced performance
        max_iter=5000,  # Sufficient iterations for test scenarios
        collision_margin=0.18  # Standard collision margin
    )

@pytest.mark.integration
def test_planner_implements_base_interface(planner):
    """Test that the planner correctly implements the BasePathPlanner interface"""
    # Verify inheritance
    assert isinstance(planner, BasePathPlanner), "Planner must inherit from BasePathPlanner"

    # Test that all required methods exist and are callable
    required_methods = [
        'set_start', 'set_goal', 'set_speed', 'set_obstacles', 'set_map_area',
        'plan', 'update', 'get_path', 'clear'
    ]

    for method_name in required_methods:
        assert hasattr(planner, method_name), f"Planner must implement {method_name}"
        assert callable(getattr(planner, method_name)), f"{method_name} must be callable"


@pytest.mark.integration
def test_planner_basic_workflow(planner):
    """Test the complete planner workflow using the abstract interface"""
    config = PlannerTestConfig.SIMPLE_SCENARIO

    # Configure planner
    planner.set_start(config['start'])
    planner.set_goal(config['goal'])
    planner.set_speed(config['speed'])
    planner.set_obstacles(config['obstacles'])
    planner.set_map_area(config['map_area'])

    # Generate path
    path = planner.plan()

    # Verify basic path properties
    assert path is not None, "Planner should generate a path"
    assert len(path) > 0, "Generated path should not be empty"

    # Verify path endpoints (convert to list for comparison if needed)
    path_start = list(path[0]) if isinstance(path[0], (tuple, np.ndarray)) else path[0]
    path_end = list(path[-1]) if isinstance(path[-1], (tuple, np.ndarray)) else path[-1]

    assert path_start == list(config['start']), "Path should start at the specified start position"
    assert path_end == list(config['goal']), "Path should end at the specified goal position"

    # Test get_path consistency
    retrieved_path = planner.get_path()
    assert retrieved_path is not None, "get_path should return the computed path"
    assert len(retrieved_path) == len(path), "Retrieved path should match planned path length"


@pytest.mark.integration
def test_planner_state_management(planner):
    """Test planner state management and clearing functionality"""
    config = PlannerTestConfig.SIMPLE_SCENARIO

    # Set up planner state
    planner.set_start(config['start'])
    planner.set_goal(config['goal'])
    planner.set_speed(config['speed'])
    planner.set_obstacles(config['obstacles'])
    planner.set_map_area(config['map_area'])

    # Generate path to populate internal state
    planner.plan()

    # Verify state is set
    assert planner.start is not None, "Start should be set"
    assert planner.goal is not None, "Goal should be set"
    assert len(planner.obstacles) > 0, "Obstacles should be set"
    assert planner.map_area is not None, "Map area should be set"

    # Clear planner state
    planner.clear()

    # Verify state is cleared
    assert planner.get_path() is None, "Path should be cleared"
    assert planner.start is None, "Start should be cleared"
    assert planner.goal is None, "Goal should be cleared"
    assert planner.obstacles == [], "Obstacles should be cleared"
    assert planner.map_area is None, "Map area should be cleared"


@pytest.mark.integration
def test_planner_update_functionality(planner):
    """Test planner update method (for reactive planners)"""
    config = PlannerTestConfig.SIMPLE_SCENARIO

    # Set up and plan initial path
    planner.set_start(config['start'])
    planner.set_goal(config['goal'])
    planner.set_speed(config['speed'])
    planner.set_obstacles(config['obstacles'])
    planner.set_map_area(config['map_area'])
    planner.plan()

    # Test update method - should not raise an exception
    # The exact behavior depends on the planner implementation
    try:
        planner.update((1, 1, 0))  # Generic state update
    except NotImplementedError:
        pytest.skip("Update method not implemented for this planner")
    except Exception as e:
        pytest.fail(f"Update method should not raise unexpected exceptions: {e}")


@pytest.mark.integration
@pytest.mark.parametrize("scenario_name,scenario_config", [
    ("no_obstacles", PlannerTestConfig.NO_OBSTACLES_SCENARIO),
    ("dense_obstacles", PlannerTestConfig.DENSE_OBSTACLES_SCENARIO),
])
def test_planner_different_scenarios(planner, scenario_name, scenario_config):
    """Test planner with different obstacle configurations"""
    # Configure planner
    planner.set_start(scenario_config['start'])
    planner.set_goal(scenario_config['goal'])
    planner.set_speed(scenario_config['speed'])
    planner.set_obstacles(scenario_config['obstacles'])
    planner.set_map_area(scenario_config['map_area'])

    # Plan path
    path = planner.plan()

    # Basic validation - planner should handle all scenarios gracefully
    assert path is not None, f"Planner should handle {scenario_name} scenario"

    # For scenarios where a path should definitely exist (no obstacles),
    # we can be more strict about validation
    if scenario_name == "no_obstacles":
        assert len(path) > 0, "Path should not be empty when no obstacles present"


@pytest.mark.integration
def test_planner_input_validation(planner):
    """Test planner behavior with various input types and edge cases"""
    # Test with different input formats
    test_cases = [
        {
            'start': (0.0, 0.0),
            'goal': (5.0, 5.0),
            'speed': (1.5, 1.5),
            'map_area': (10, 10),
            'obstacles': []
        },
        {
            'start': [1.5, 1.5],
            'goal': [7.5, 4.5],
            'speed': (1.0, 0.7),
            'map_area': (10, 8),
            'obstacles': [(2, 2), (3, 3)]
        }
    ]

    for i, case in enumerate(test_cases):
        # Clear previous state
        planner.clear()

        # Configure with current test case
        planner.set_start(case['start'])
        planner.set_goal(case['goal'])
        planner.set_speed(case['speed'])
        planner.set_obstacles(case['obstacles'])
        planner.set_map_area(case['map_area'])

        # Should not raise exceptions
        try:
            path = planner.plan()
            assert path is not None, f"Test case {i} should produce a valid result"
        except Exception as e:
            pytest.fail(f"Test case {i} raised unexpected exception: {e}")


@pytest.mark.integration
def test_planner_path_properties(planner):
    """Test basic properties of generated paths"""
    config = PlannerTestConfig.NO_OBSTACLES_SCENARIO

    planner.set_start(config['start'])
    planner.set_goal(config['goal'])
    planner.set_speed(config['speed'])
    planner.set_obstacles(config['obstacles'])
    planner.set_map_area(config['map_area'])

    path = planner.plan()

    if path and len(path) > 1:
        # Path should be a sequence of points
        assert hasattr(path, '__iter__'), "Path should be iterable"

        # Each point should have at least 2 dimensions (x, y)
        for i, point in enumerate(path):
            assert len(point) >= 2, f"Point {i} should have at least 2 dimensions"

        # Path points should be within map boundaries (basic sanity check)
        map_width, map_height = config['map_area']
        for i, point in enumerate(path):
            x, y = point[0], point[1]
            assert 0 <= x <= map_width, f"Point {i} x-coordinate should be within map bounds"
            assert 0 <= y <= map_height, f"Point {i} y-coordinate should be within map bounds"