import pytest
import numpy as np
from neonfc_ssl.control_layer.path_planning.base_planner import BasePathPlanner
from neonfc_ssl.control_layer.path_planning.rrt.rrt_planner import RRTPlanner


@pytest.fixture
def planner():
    """Fixture that returns a planner instance"""
    return RRTPlanner(step_size=0.1, max_iter=5000, collision_margin=0.18)

@pytest.mark.integration
def test_planner_interface(planner):
    """Test that RRTPlanner implements the BasePathPlanner interface correctly"""
    # Test that all abstract methods are implemented
    assert hasattr(planner, 'set_start')
    assert hasattr(planner, 'set_goal')
    assert hasattr(planner, 'set_obstacles')
    assert hasattr(planner, 'set_map_area')
    assert hasattr(planner, 'plan')
    assert hasattr(planner, 'update')
    assert hasattr(planner, 'get_path')
    assert hasattr(planner, 'clear')

@pytest.mark.integration
def test_planner_workflow(planner):
    """Test the complete planner workflow through the abstract interface"""
    # Setup test scenario
    start = (0.5, 0.5)
    goal = (8.5, 5.5)
    map_area = (9, 6)

    # Create simple obstacles (avoiding rectangle utility method)
    obstacles = [(3, 3), (3, 4), (4, 3), (4, 4), (6, 4), (7, 4)]

    # Configure planner through abstract interface
    planner.set_start(start)
    planner.set_goal(goal)
    planner.set_obstacles(obstacles)
    planner.set_map_area(map_area)

    # Generate path through abstract interface
    path = planner.plan()

    # Verify results through abstract interface
    assert path is not None, "Path should be generated"
    assert len(path) > 0, "Path should not be empty"
    assert path[0] == list(start), "Path should start at start position"
    assert path[-1] == list(goal), "Path should end at goal position"

    # Test get_path method
    assert planner.get_path() == path, "get_path should return the computed path"

    # Test update method (should not raise an exception)
    planner.update((1, 1, 0))

    # Test clear method
    planner.clear()
    assert planner.get_path() is None, "Planner should be cleared"
    assert planner.start is None, "Start should be cleared"
    assert planner.goal is None, "Goal should be cleared"
    assert planner.obstacles == [], "Obstacles should be cleared"
    assert planner.map_area is None, "Map area should be cleared"

@pytest.mark.integration
def test_planner_with_different_configurations(planner):
    """Test planner with different parameter configurations"""
    # Test with different step sizes
    planner.step_size = 0.1
    planner.max_iter = 1000
    planner.collision_margin = 0.2

    planner.set_start((1, 1))
    planner.set_goal((8, 5))
    planner.set_obstacles([])
    planner.set_map_area((9, 6))

    path = planner.plan()
    assert path is not None, "Path should be generated with different parameters"

@pytest.mark.integration
def test_planner_with_no_obstacles(planner):
    """Test planner with no obstacles"""
    planner.set_start((1, 1))
    planner.set_goal((8, 5))
    planner.set_obstacles([])
    planner.set_map_area((9, 6))

    path = planner.plan()
    assert path is not None, "Path should be generated with no obstacles"
    assert len(path) > 0, "Path should not be empty"

@pytest.mark.integration
def test_planner_with_dense_obstacles(planner):
    """Test planner with dense obstacles that might block the path"""
    # Create a wall of obstacles
    obstacles = [(x, y) for x in range(4, 6) for y in range(0, 7)]

    planner.set_start((1, 3))
    planner.set_goal((8, 3))
    planner.set_obstacles(obstacles)
    planner.set_map_area((9, 6))

    path = planner.plan()
    # The path might be empty if obstacles completely block the way
    # This test just ensures the planner doesn't crash
    assert path is not None, "Planner should handle dense obstacles"
